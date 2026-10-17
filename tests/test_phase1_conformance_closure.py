    assert response.status_code == expected_status, response.text


@pytest.mark.skipif(not os.getenv("CRR_DATABASE_URL"), reason="requires PostgreSQL CI database")
def test_postgresql_parallel_successor_creation_has_one_winner() -> None:
    database_url = os.environ["CRR_DATABASE_URL"]
    engine = create_engine(database_url, pool_size=5, max_overflow=5)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex[:12]
    org_id = f"org_concurrency_{suffix}"
    actor_id = f"act_{org_id}"
    token = f"token-{suffix}"
    with factory.begin() as session:
        session.add(Organization(id=org_id, name=org_id, status="ACTIVE", created_at=NOW))
        session.flush()
        session.add(
            Actor(
                id=actor_id,
                organization_id=org_id,
                name="Admin",
                role="ORG_ADMIN",
                active=True,
                created_at=NOW,
            )
        )
        session.flush()
        session.add(
            APIKey(
                id=f"key_{suffix}",
                organization_id=org_id,
                actor_id=actor_id,
                secret_hash=sha256(token.encode()).hexdigest(),
                scopes=["admin:*"],
                revoked=False,
                created_at=NOW,
            )
        )
        session.add(
            Location(
                id=f"loc_{suffix}",
                organization_id=org_id,
                name="Yard",