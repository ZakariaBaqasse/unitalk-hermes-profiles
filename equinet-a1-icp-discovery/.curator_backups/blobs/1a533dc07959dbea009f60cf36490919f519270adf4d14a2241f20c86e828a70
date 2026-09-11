# Twenty staging readiness

The lean A1 path requires only:

1. live Twenty MCP access to `find_many_companies`, `find_one_company`, `create_many_companies`, and `update_one_company`;
2. the approved current Company field mapping;
3. deterministic duplicate preflight by discovery fingerprint, then verified website when present;
4. UUID-scoped updates that preserve human review status;
5. read-back verification for every write;
6. one terminal disposition per returned lead in a complete staging index.

Website evidence, ICP scores, custom reviewer fields, exports and a saved view are not prerequisites for Company staging. They may be added later without changing the retrieval path.

Never retry an uncertain Company or Person create blindly. Never create Twenty objects outside the Company plus optional linked Person path. Production status still requires the active published discovery workflow and schema-valid terminal entity index.
