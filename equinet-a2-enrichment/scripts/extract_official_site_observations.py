#!/usr/bin/env python3
"""Deterministically extract official-site observations without business decisions."""
from __future__ import annotations

import argparse
import html as html_module
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

from build_official_site_plan import load_json, sha256_json, utc_now, write_json_atomic

EMAIL_RE = re.compile(r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63})(?![\w.-])", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.()/-]*)?(?:\(?\d{2,4}\)?[\s.()/-]*){2,4}\d{2,4}(?!\w)")
COMBINED_PERSON_RE = re.compile(
    r"^(?P<name>[A-ZÀ-ÖØ-Þ][\wÀ-ÖØ-öø-ÿ'’.-]+(?:\s+[A-ZÀ-ÖØ-Þ][\wÀ-ÖØ-öø-ÿ'’.-]+){1,4})\s*(?:—|–|\||,)\s*(?P<role>[^@]{2,120})$"
)
SOCIAL_DOMAINS = {
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "instagram.com": "instagram",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "linkedin.com": "linkedin",
    "tiktok.com": "tiktok",
    "x.com": "x",
    "twitter.com": "x",
}
NON_NAME_WORDS = {
    "about", "contact", "team", "staff", "leadership", "directory", "home", "services", "our", "meet", "people",
    "facebook", "instagram", "youtube", "linkedin", "tiktok", "twitter", "copyright", "privacy", "terms",
}
ROLE_HINT_RE = re.compile(r"\b(owner|founder|farrier|manager|director|coordinator|trainer|coach|rider|liaison|receptionist|veterinary|officer|assistant|president|staff)\b", re.I)
RELATIONSHIP_RE = re.compile(r"\b(owner|owned|operated|operator|founder|founded|runs?|manages?|manager|director|president|team|staff|craftsman|employee)\b", re.I)
NAME_TOKEN = r"[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+"
SHARED_SURNAME_RE = re.compile(rf"\b(?P<first1>{NAME_TOKEN})\s+(?:and|&)\s+(?P<first2>{NAME_TOKEN})\s+(?P<last>{NAME_TOKEN})\b")
FULL_NAME_PAIR_RE = re.compile(rf"\b(?P<name1>{NAME_TOKEN}\s+{NAME_TOKEN})\s*(?:and|&)\s*(?P<name2>{NAME_TOKEN}\s+{NAME_TOKEN})\b")
INDIVIDUAL_ROLE_RE = re.compile(rf"\b(?P<name>{NAME_TOKEN}\s+{NAME_TOKEN})\s+(?P<relation>(?i:is\s+(?:an?|the)\s+[^.;]{{2,300}}|runs?\s+[^.;]{{2,300}}|manages?\s+[^.;]{{2,300}}|owns?\s+[^.;]{{2,300}}|oversees?\s+[^.;]{{2,300}}))")
NON_PERSON_TOKENS = {"leather", "tack", "shop", "street", "kentucky", "custom", "goods", "main", "sale", "halter", "halters", "inc", "shank", "snap", "bull", "belt", "collar", "pouch", "turnout", "bridle", "neck", "strap", "cover", "plate", "gifts", "pads"}


class ObservationError(ValueError):
    pass


class VisibleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.headings: list[tuple[str, str]] = []
        self._skip_depth = 0
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []
        self._heading_tag: str | None = None
        self._heading_text: list[str] = []
        self._semantic_skip_depth = 0
        self._block_tag: str | None = None
        self._block_text: list[str] = []
        self.blocks: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered in {"script", "style", "noscript", "template", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if lowered in {"nav", "footer", "header", "aside", "form"}:
            self._semantic_skip_depth += 1
        if not self._semantic_skip_depth and lowered in {"p", "h2", "h3", "h4", "h5", "h6"} and self._block_tag is None:
            self._block_tag = lowered
            self._block_text = []
        if lowered == "a":
            self._anchor_href = next((value for key, value in attrs if key.casefold() == "href"), None)
            self._anchor_text = []
        if lowered in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_tag = lowered
            self._heading_text = []

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered in {"script", "style", "noscript", "template", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if lowered == self._block_tag:
            text = re.sub(r"\s+", " ", " ".join(self._block_text)).strip()
            if text:
                self.blocks.append((self._block_tag or "", text))
            self._block_tag = None
            self._block_text = []
        if lowered in {"nav", "footer", "header", "aside", "form"} and self._semantic_skip_depth:
            self._semantic_skip_depth -= 1
        if lowered == "a" and self._anchor_href is not None:
            self.links.append((self._anchor_href, " ".join(self._anchor_text).strip()))
            self._anchor_href = None
            self._anchor_text = []
        if lowered == self._heading_tag:
            text = " ".join(self._heading_text).strip()
            if text:
                self.headings.append((self._heading_tag or "", text))
            self._heading_tag = None
            self._heading_text = []
        if lowered in {"p", "div", "li", "address", "footer", "section", "article", "br", "tr", "td", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.lines.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = html_module.unescape(data)
        if text.strip():
            self.lines.append(text)
            if self._anchor_href is not None:
                self._anchor_text.append(text)
            if self._heading_tag is not None:
                self._heading_text.append(text)
            if self._block_tag is not None and not self._semantic_skip_depth:
                self._block_text.append(text)

    def visible_lines(self) -> list[str]:
        joined = " ".join(self.lines)
        return [re.sub(r"\s+", " ", line).strip() for line in joined.split("\n") if line.strip()]


def platform_for(url: str) -> str | None:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.casefold().rstrip(".")
    for domain, platform in SOCIAL_DOMAINS.items():
        if host == domain or host.endswith("." + domain):
            return platform
    return None


def evidence(page: dict[str, Any], text: str) -> dict[str, Any]:
    return {
        "page_index": page["page_index"],
        "page_url": page["resolved_url"],
        "page_title": page.get("title"),
        "evidence_text": text[:500],
        "page_content_sha256": page.get("content_sha256"),
    }


def observation_id(kind: str, value: Any, page_url: str) -> str:
    digest = sha256_json({"kind": kind, "value": value, "page_url": page_url})[:16]
    return f"website-{kind}-{digest}"


def _looks_like_name(text: str) -> bool:
    cleaned = text.strip().strip("-–—|,:")
    words = cleaned.split()
    if not 2 <= len(words) <= 5 or len(cleaned) > 100:
        return False
    if any(word.casefold().strip(".,") in NON_NAME_WORDS for word in words):
        return False
    return all(re.match(r"^[A-ZÀ-ÖØ-Þ][\wÀ-ÖØ-öø-ÿ'’.-]*$", word) is not None for word in words)


def _looks_like_role(text: str) -> bool:
    cleaned = text.strip()
    if not 2 <= len(cleaned) <= 120:
        return False
    if EMAIL_RE.search(cleaned) or PHONE_RE.fullmatch(cleaned) or cleaned.startswith(("http://", "https://")):
        return False
    return len(cleaned.split()) <= 15


def _page_content(page: dict[str, Any]) -> tuple[list[str], list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    parser = VisibleHTMLParser()
    html = page.get("html")
    if isinstance(html, str) and html:
        parser.feed(html)
    lines = parser.visible_lines()
    headings = list(parser.headings)
    markdown = page.get("markdown")
    if isinstance(markdown, str) and markdown:
        markdown_lines = [re.sub(r"\s+", " ", re.sub(r"^#{1,6}\s*", "", line)).strip() for line in markdown.splitlines() if line.strip()]
        for raw_line, cleaned in zip((line for line in markdown.splitlines() if line.strip()), markdown_lines):
            heading_match = re.match(r"^\s*(#{1,6})\s+", raw_line)
            if heading_match:
                headings.append((f"markdown-h{len(heading_match.group(1))}", cleaned))
        for line in markdown_lines:
            if line not in lines:
                lines.append(line)
    links = list(parser.links)
    blocks = list(parser.blocks)
    if not blocks and isinstance(markdown, str):
        for raw in re.split(r"\n\s*\n", markdown):
            cleaned = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", raw)
            cleaned = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", cleaned)
            cleaned = re.sub(r"^#{1,6}\s*", "", cleaned.strip())
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" -*")
            if len(cleaned) >= 20:
                blocks.append(("markdown-block", cleaned))
    raw_links = page.get("links")
    if isinstance(raw_links, list):
        for item in raw_links:
            if isinstance(item, str):
                links.append((item, ""))
            elif isinstance(item, dict) and isinstance(item.get("url") or item.get("href"), str):
                links.append((item.get("url") or item.get("href"), str(item.get("text") or item.get("title") or "")))
    return lines, links, headings, blocks


def _semantic_evidence_blocks(blocks: list[tuple[str, str]], page: dict[str, Any]) -> list[dict[str, Any]]:
    category = str(page.get("category") or "").casefold()
    page_identity = (str(page.get("resolved_url") or "") + " " + str(page.get("title") or "")).casefold()
    dedicated_page = (
        (category == "about" and "about" in page_identity)
        or (category == "team" and bool(re.search(r"\b(team|people|leadership)\b", page_identity)))
        or (category == "staff" and "staff" in page_identity)
    )
    candidates: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for source_index, (tag, raw) in enumerate(blocks):
        text = re.sub(r"\s+", " ", raw).strip()
        if not 20 <= len(text) <= 2000 or text.casefold() in seen:
            continue
        seen.add(text.casefold())
        has_relationship = bool(RELATIONSHIP_RE.search(text))
        has_name_shape = bool(SHARED_SURNAME_RE.search(text) or FULL_NAME_PAIR_RE.search(text) or INDIVIDUAL_ROLE_RE.search(text))
        if not dedicated_page and not (has_relationship and has_name_shape):
            continue
        score = (4 if has_relationship else 0) + (4 if has_name_shape else 0) + (2 if tag.startswith("h") else 0)
        candidates.append((score, source_index, text))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    result = []
    for _, source_index, text in candidates[:12]:
        block_id = observation_id("person-block", {"text": text, "index": source_index}, page["resolved_url"])
        result.append({
            "block_id": block_id,
            "page_index": page["page_index"],
            "page_url": page["resolved_url"],
            "page_title": page.get("title"),
            "page_content_sha256": page.get("content_sha256"),
            "source_index": source_index,
            "text": text,
            "untrusted_source_content": True,
        })
    return result


def _prose_person_candidates(block: dict[str, Any], page: dict[str, Any]) -> list[dict[str, Any]]:
    text = block["text"]
    candidates: list[tuple[str, str | None, str, str]] = []
    for match in SHARED_SURNAME_RE.finditer(text):
        prefix = text[:match.start()].rstrip()
        if re.search(rf"{NAME_TOKEN}$", prefix):
            continue
        tokens = {match.group("first1").casefold(), match.group("first2").casefold(), match.group("last").casefold()}
        if tokens & NON_PERSON_TOKENS:
            continue
        mention = match.group(0)
        prefix_role = re.search(r"(?i)(owned\s+and\s+operated\s+by|co-owned\s+by|founded\s+by)\s*$", prefix[-80:])
        role = prefix_role.group(1) if prefix_role else None
        candidates.extend([
            (f"{match.group('first1')} {match.group('last')}", role, mention, "shared_surname_split"),
            (f"{match.group('first2')} {match.group('last')}", role, mention, "shared_surname_split"),
        ])
    for match in FULL_NAME_PAIR_RE.finditer(text):
        mention = match.group(0)
        tail=text[match.end():match.end()+180]
        tail_role=re.match(r"\s*(?P<role>(?i:runs?|manages?|owns?|operates?|oversees?)\s+[^.;]{2,150})",tail)
        role=tail_role.group("role").strip() if tail_role else None
        for key in ("name1", "name2"):
            name = match.group(key)
            if not ({token.casefold() for token in name.split()} & NON_PERSON_TOKENS):
                candidates.append((name, role, mention, "multiple_full_names"))
    for match in INDIVIDUAL_ROLE_RE.finditer(text):
        name = match.group("name")
        if {token.casefold() for token in name.split()} & NON_PERSON_TOKENS:
            continue
        candidates.append((name, match.group("relation").strip(), match.group(0), "prose_relationship"))
    result=[]
    for name, role, mention, method in candidates:
        value={"name":name,"role":role,"source_mention":mention,"method":method}
        result.append({
            "observation_id": observation_id("person", value, page["resolved_url"]),
            "observation_type": "candidate_person",
            "observed_name": name,
            "observed_role": role,
            "source_mention": mention,
            "extraction_method": method,
            "source_block_id": block["block_id"],
            "page_evidence": [evidence(page, text)],
            "_line_index": -1000000,
        })
    return result


def _person_candidates(lines: list[str], headings: list[tuple[str, str]], page: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    # Page-level H1s normally name the Company/page, not a person. Team-card
    # headings begin at H2; combined "Name — Role" lines remain eligible.
    heading_values = {text for tag, text in headings if tag not in {"h1", "markdown-h1"}}
    h1_values = {text for tag, text in headings if tag in {"h1", "markdown-h1"}}
    page_category=str(page.get("category") or "").casefold()
    page_identity=(str(page.get("resolved_url") or "")+" "+str(page.get("title") or "")).casefold()
    dedicated_people_page=page_category in {"team","staff"} and bool(re.search(r"\b(team|staff|people|leadership)\b",page_identity))
    for index, line in enumerate(lines):
        match = COMBINED_PERSON_RE.match(line)
        if match and _looks_like_name(match.group("name")) and not ROLE_HINT_RE.search(match.group("name")) and _looks_like_role(match.group("role")) and ROLE_HINT_RE.search(match.group("role")):
            name, role = match.group("name").strip(), match.group("role").strip()
            candidates.append({"name": name, "role": role, "line_index": index, "text": line})
            continue
        if (line in heading_values or dedicated_people_page) and line not in h1_values and not ROLE_HINT_RE.search(line) and _looks_like_name(line):
            role = next((lines[j].strip() for j in range(index + 1, min(index + 4, len(lines))) if _looks_like_role(lines[j]) and ROLE_HINT_RE.search(lines[j])), None)
            if role or dedicated_people_page:
                candidates.append({"name": line.strip(), "role": role, "line_index": index, "text": f"{line} — {role}" if role else line})
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (candidate["name"].casefold(), (candidate.get("role") or '').casefold())
        unique.setdefault(key, candidate)
    result: list[dict[str, Any]] = []
    for candidate in unique.values():
        value = {"name": candidate["name"], "role": candidate.get("role")}
        result.append({
            "observation_id": observation_id("person", value, page["resolved_url"]),
            "observation_type": "candidate_person",
            "observed_name": candidate["name"],
            "observed_role": candidate.get("role"),
            "page_evidence": [evidence(page, candidate["text"])],
            "_line_index": candidate["line_index"],
        })
    return result


def extract_observations(fetch: dict[str, Any]) -> dict[str, Any]:
    if fetch.get("schema_id") != "a2-firecrawl-official-site-fetch":
        raise ObservationError("input is not an official-site fetch artifact")
    if fetch.get("status") not in {"succeeded", "partial"}:
        raise ObservationError("official-site fetch did not produce usable collected pages")
    pages = fetch.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ObservationError("fetch artifact has no pages")
    if len(pages) > 5 or fetch.get("page_count") != len(pages):
        raise ObservationError("fetch artifact violates the five-page bound")
    contacts_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    socials_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    people_by_key: dict[str, dict[str, Any]] = {}
    person_evidence_blocks: list[dict[str, Any]] = []
    source_pages: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict) or page.get("status") != "collected" or not isinstance(page.get("resolved_url"), str):
            continue
        if not isinstance(page.get("page_index"), int):
            raise ObservationError("collected page lacks page_index")
        source_pages.append({key: page.get(key) for key in ("page_index", "category", "resolved_url", "title", "content_sha256")})
        lines, links, headings, semantic_blocks = _page_content(page)
        page_blocks = _semantic_evidence_blocks(semantic_blocks, page)
        person_evidence_blocks.extend(page_blocks)
        page_people = _person_candidates(lines, headings, page)
        for block in page_blocks:
            page_people.extend(_prose_person_candidates(block, page))
        for person in page_people:
            key = person["observed_name"].casefold()
            existing = people_by_key.get(key)
            if existing:
                existing["page_evidence"].extend(item for item in person["page_evidence"] if item not in existing["page_evidence"])
                role=person.get("observed_role")
                if role and role not in existing["observed_role_candidates"]:
                    existing["observed_role_candidates"].append(role)
                if not existing.get("observed_role") and role:
                    existing["observed_role"]=role
                mention=person.get("source_mention")
                if mention and mention not in existing["source_mentions"]:
                    existing["source_mentions"].append(mention)
            else:
                person["observed_role_candidates"]=[person["observed_role"]] if person.get("observed_role") else []
                person["source_mentions"]=[person["source_mention"]] if person.get("source_mention") else []
                people_by_key[key] = person
        for line_index, line in enumerate(lines):
            for email_match in EMAIL_RE.finditer(line):
                raw = email_match.group(1)
                key = ("email", raw.casefold())
                nearby = min(page_people, key=lambda person: abs(person["_line_index"] - line_index), default=None)
                nearby_id = nearby["observation_id"] if nearby and 0 <= line_index - nearby["_line_index"] <= 3 else None
                item = contacts_by_key.get(key)
                if item:
                    item["page_evidence"].append(evidence(page, line))
                else:
                    contacts_by_key[key] = {
                        "observation_id": observation_id("contact", {"type": "email", "value": raw}, page["resolved_url"]),
                        "observation_type": "contact",
                        "contact_type": "email",
                        "observed_value": raw,
                        "observed_context": {"nearby_person_observation_id": nearby_id},
                        "page_evidence": [evidence(page, line)],
                    }
            for phone_match in PHONE_RE.finditer(line):
                raw = phone_match.group(0).strip(" .,;:-")
                digits = re.sub(r"\D", "", raw)
                if not 7 <= len(digits) <= 15:
                    continue
                key = ("phone", digits)
                nearby = min(page_people, key=lambda person: abs(person["_line_index"] - line_index), default=None)
                nearby_id = nearby["observation_id"] if nearby and 0 <= line_index - nearby["_line_index"] <= 3 else None
                item = contacts_by_key.get(key)
                if item:
                    item["page_evidence"].append(evidence(page, line))
                else:
                    contacts_by_key[key] = {
                        "observation_id": observation_id("contact", {"type": "phone", "value": raw}, page["resolved_url"]),
                        "observation_type": "contact",
                        "contact_type": "phone",
                        "observed_value": raw,
                        "observed_context": {"nearby_person_observation_id": nearby_id},
                        "page_evidence": [evidence(page, line)],
                    }
        for href, link_text in links:
            absolute = urljoin(page["resolved_url"], href.strip()) if isinstance(href, str) else ""
            platform = platform_for(absolute)
            if not platform:
                continue
            parsed = urlsplit(absolute)
            exact_url = parsed._replace(fragment="").geturl()
            key = (platform, exact_url)
            item = socials_by_key.get(key)
            page_ev = evidence(page, link_text.strip() or exact_url)
            if item:
                item["page_evidence"].append(page_ev)
            else:
                socials_by_key[key] = {
                    "observation_id": observation_id("social", {"platform": platform, "url": exact_url}, page["resolved_url"]),
                    "observation_type": "social_link",
                    "platform": platform,
                    "observed_url": exact_url,
                    "page_evidence": [page_ev],
                }
    people = []
    for item in people_by_key.values():
        item.pop("_line_index", None)
        people.append(item)
    contacts = list(contacts_by_key.values())
    socials = list(socials_by_key.values())
    result: dict[str, Any] = {
        "schema_id": "a2-official-site-observations",
        "schema_version": "0.1.0",
        "created_at": utc_now(),
        "status": "observed",
        "run_id": fetch.get("run_id"),
        "company_id": fetch.get("company_id"),
        "company": fetch.get("company"),
        "official_url": fetch.get("official_url"),
        "source_id": "prospect_official_website",
        "source_fetch_sha256": fetch.get("artifact_sha256"),
        "source_pages": source_pages,
        "contacts": sorted(contacts, key=lambda item: item["observation_id"]),
        "social_links": sorted(socials, key=lambda item: item["observation_id"]),
        "candidate_people": sorted(people, key=lambda item: item["observation_id"]),
        "person_evidence_blocks": sorted(person_evidence_blocks, key=lambda item: (item["page_index"], item["source_index"])),
        "person_extraction_coverage": {
            "status": "pending_llm_observation_proposals" if person_evidence_blocks else "complete_no_relevant_blocks",
            "semantic_block_count": len(person_evidence_blocks),
            "deterministic_candidate_count": len(people),
            "llm_observation_proposals_validated": False,
        },
        "summary": {"contacts": len(contacts), "social_links": len(socials), "candidate_people": len(people)},
        "business_decisions_made": False,
        "role_classification_performed": False,
        "external_calls": 0,
        "external_actions": 0,
        "errors": [],
    }
    result["artifact_sha256"] = sha256_json({key: value for key, value in result.items() if key != "artifact_sha256"})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fetch", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = extract_observations(load_json(args.fetch))
        code = 0
    except Exception as exc:
        result = {"schema_id": "a2-official-site-observations", "status": "invalid", "errors": [str(exc)], "external_calls": 0, "external_actions": 0}
        code = 1
    write_json_atomic(args.output, result)
    print(__import__("json").dumps({"status": result["status"], "summary": result.get("summary"), "errors": result.get("errors", []), "output": str(args.output)}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
