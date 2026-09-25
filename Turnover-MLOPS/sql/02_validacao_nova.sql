-- =====================================================================
-- AULA 2 -- a validacao da populacao nova
--
--     psql turnover -U postgres -f sql/02_validacao_nova.sql
--
-- Na Aula 1 existia UM conjunto de teste: validacao_congelada, o mundo antigo.
-- Agora a populacao mudou, e um modelo feito para o mundo novo precisa ser
-- julgado por um juiz que conheca o mundo novo. Esta tabela e esse juiz.
--
-- Repare: a antiga NAO e apagada. As duas convivem, e escolher entre elas
-- passa a ser uma decisao que voce registra -- e o assunto da aula.
-- =====================================================================

CREATE TABLE IF NOT EXISTS validacao_nova (
    id_pessoa                    TEXT PRIMARY KEY,
    abs_eventos                  DOUBLE PRECISION NOT NULL DEFAULT 0,
    abs_qtd_total                DOUBLE PRECISION NOT NULL DEFAULT 0,
    horas_previstas_total        DOUBLE PRECISION NOT NULL DEFAULT 0,
    acidentes_eventos            DOUBLE PRECISION NOT NULL DEFAULT 0,
    acidentes_com_afastamento    DOUBLE PRECISION NOT NULL DEFAULT 0,
    acidentes_dias_perdidos      DOUBLE PRECISION NOT NULL DEFAULT 0,
    he_eventos                   DOUBLE PRECISION NOT NULL DEFAULT 0,
    he_referencia_total          DOUBLE PRECISION NOT NULL DEFAULT 0,
    he_valor_total               DOUBLE PRECISION NOT NULL DEFAULT 0,
    hi_eventos                   DOUBLE PRECISION NOT NULL DEFAULT 0,
    hi_minutos_irregulares       DOUBLE PRECISION NOT NULL DEFAULT 0,
    hi_minutos_extras            DOUBLE PRECISION NOT NULL DEFAULT 0,
    mov_sal_eventos              DOUBLE PRECISION NOT NULL DEFAULT 0,
    mov_sal_valor_total          DOUBLE PRECISION NOT NULL DEFAULT 0,
    mov_sal_perc_medio           DOUBLE PRECISION NOT NULL DEFAULT 0,
    pediu_para_sair              SMALLINT NOT NULL,
    origem                       TEXT     NOT NULL   -- de qual lote saiu
);

-- Para recomecar:  DROP TABLE IF EXISTS validacao_nova;
