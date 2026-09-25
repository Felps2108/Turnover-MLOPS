-- Corrige objetos do MLflow que tenham sido criados pelo superusuario
-- postgres antes de a aplicacao passar a usar o usuario turnover.
DO $$
DECLARE
    objeto record;
BEGIN
    FOR objeto IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format(
            'ALTER TABLE public.%I OWNER TO turnover',
            objeto.tablename
        );
    END LOOP;

    FOR objeto IN
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    LOOP
        EXECUTE format(
            'ALTER SEQUENCE public.%I OWNER TO turnover',
            objeto.sequence_name
        );
    END LOOP;
END
$$;

GRANT USAGE, CREATE ON SCHEMA public TO turnover;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO turnover;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO turnover;
