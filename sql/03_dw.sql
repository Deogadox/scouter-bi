/* =====================================================================
   Scouter BI — 03_dw.sql
   Modelo estrela (schema dw) + procedure de carga stg -> dw.

   Dimensões: dim_personagem, dim_saga, dim_transformacao, dim_planeta
   Fatos:     fato_poder (personagem x saga x forma), fato_luta (luta canônica)

   dw.sp_carga_dw recarrega tudo numa transação e faz testes antes e
   depois. Se algum teste falhar, desfaz a carga e registra ERRO no log.
   ===================================================================== */
USE DBZ_BI;
GO

/* ------------------------------------------------------------ dimensões */
IF OBJECT_ID(N'dw.dim_planeta', N'U') IS NULL
CREATE TABLE dw.dim_planeta (
    sk_planeta   INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_dim_planeta PRIMARY KEY,
    id_api       INT           NOT NULL,
    nome         NVARCHAR(100) NOT NULL,
    destruido    BIT           NULL,
    url_imagem   NVARCHAR(400) NULL
);
GO

IF OBJECT_ID(N'dw.dim_personagem', N'U') IS NULL
CREATE TABLE dw.dim_personagem (
    sk_personagem      INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_dim_personagem PRIMARY KEY,
    id_api             INT            NULL,
    codigo_extra       VARCHAR(40)    NULL,
    nome               NVARCHAR(100)  NOT NULL,
    raca               NVARCHAR(50)   NULL,
    genero             NVARCHAR(20)   NULL,
    afiliacao          NVARCHAR(60)   NULL,
    sk_planeta         INT            NULL,
    url_imagem         NVARCHAR(400)  NULL,
    ki_api_valor       DECIMAL(38,0)  NULL,
    ki_api_status      VARCHAR(20)    NULL,
    ki_max_api_valor   DECIMAL(38,0)  NULL,
    ki_max_api_status  VARCHAR(20)    NULL,
    origem             VARCHAR(20)    NOT NULL   -- api | curadoria
);
GO

IF OBJECT_ID(N'dw.dim_saga', N'U') IS NULL
CREATE TABLE dw.dim_saga (
    sk_saga            INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_dim_saga PRIMARY KEY,
    codigo_saga        VARCHAR(30)   NOT NULL,
    nome               NVARCHAR(80)  NOT NULL,
    serie              VARCHAR(10)   NOT NULL,
    arco               NVARCHAR(40)  NOT NULL,
    ordem_cronologica  SMALLINT      NOT NULL,
    episodio_inicio    SMALLINT      NULL,
    episodio_fim       SMALLINT      NULL,
    filler             BIT           NOT NULL
);
GO

/* Grão: personagem x forma. "Base" é uma forma como as outras. */
IF OBJECT_ID(N'dw.dim_transformacao', N'U') IS NULL
CREATE TABLE dw.dim_transformacao (
    sk_transformacao  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_dim_transformacao PRIMARY KEY,
    sk_personagem     INT            NOT NULL,
    forma             NVARCHAR(100)  NOT NULL,
    e_base            BIT            NOT NULL,
    ordem             SMALLINT       NOT NULL,
    id_api            INT            NULL,
    nome_api          NVARCHAR(100)  NULL,
    ki_api_valor      DECIMAL(38,0)  NULL,
    url_imagem        NVARCHAR(400)  NULL,
    origem            VARCHAR(20)    NOT NULL   -- curadoria | api
);
GO

/* ----------------------------------------------------------------- fatos */
IF OBJECT_ID(N'dw.fato_poder', N'U') IS NULL
CREATE TABLE dw.fato_poder (
    sk_personagem      INT            NOT NULL,
    sk_saga            INT            NOT NULL,
    sk_transformacao   INT            NOT NULL,
    nivel_poder        DECIMAL(38,0)  NOT NULL,
    nivel_poder_log10  FLOAT          NULL,
    fonte_valor        VARCHAR(20)    NOT NULL,
    referencia         NVARCHAR(200)  NULL,
    observacao         NVARCHAR(300)  NULL,
    CONSTRAINT PK_fato_poder PRIMARY KEY (sk_personagem, sk_saga, sk_transformacao)
);
GO

IF OBJECT_ID(N'dw.fato_luta', N'U') IS NULL
CREATE TABLE dw.fato_luta (
    id_luta                     INT            NOT NULL CONSTRAINT PK_fato_luta PRIMARY KEY,
    sk_saga                     INT            NOT NULL,
    sk_vencedor                 INT            NOT NULL,
    sk_transformacao_vencedor   INT            NOT NULL,
    sk_perdedor                 INT            NOT NULL,
    sk_transformacao_perdedor   INT            NOT NULL,
    resultado                   VARCHAR(20)    NOT NULL,
    poder_vencedor              DECIMAL(38,0)  NULL,
    poder_perdedor              DECIMAL(38,0)  NULL,
    zebra                       BIT            NOT NULL,
    episodio                    SMALLINT       NULL,
    observacao                  NVARCHAR(300)  NULL
);
GO

/* ------------------------------------------------------------- procedure */
CREATE OR ALTER PROCEDURE dw.sp_carga_dw
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @etapa VARCHAR(100) = 'fase2_carga_dw', @id INT, @linhas INT, @msg NVARCHAR(4000);
    EXEC ctl.sp_log @etapa = @etapa, @status = 'INICIADO', @id_execucao = @id OUTPUT;

    BEGIN TRY
        /* ---------- testes ANTES: chaves da curadoria precisam existir */
        SELECT @msg = STRING_AGG(CONCAT(c.personagem, ' (id_api ', c.id_personagem_api, ')'), ', ')
        FROM (SELECT DISTINCT personagem, id_personagem_api FROM stg.cur_poder WHERE id_personagem_api IS NOT NULL) c
        WHERE NOT EXISTS (SELECT 1 FROM stg.personagem p WHERE p.id_api = c.id_personagem_api);
        IF @msg IS NOT NULL
        BEGIN
            SET @msg = N'Personagem da curadoria não existe na API: ' + @msg;
            THROW 50001, @msg, 1;
        END

        SELECT @msg = STRING_AGG(CONCAT(c.forma, ' (id_api ', c.id_transformacao_api, ')'), ', ')
        FROM (SELECT DISTINCT forma, id_transformacao_api FROM stg.cur_poder WHERE id_transformacao_api IS NOT NULL) c
        WHERE NOT EXISTS (SELECT 1 FROM stg.transformacao t WHERE t.id_api = c.id_transformacao_api);
        IF @msg IS NOT NULL
        BEGIN
            SET @msg = N'Transformação da curadoria não existe na API: ' + @msg;
            THROW 50002, @msg, 1;
        END

        BEGIN TRAN;

        TRUNCATE TABLE dw.fato_luta;
        TRUNCATE TABLE dw.fato_poder;
        TRUNCATE TABLE dw.dim_transformacao;
        TRUNCATE TABLE dw.dim_personagem;
        TRUNCATE TABLE dw.dim_saga;
        TRUNCATE TABLE dw.dim_planeta;

        /* ---------- dim_planeta */
        INSERT INTO dw.dim_planeta (id_api, nome, destruido, url_imagem)
        SELECT id_api, LTRIM(RTRIM(nome)), destruido, url_imagem
        FROM stg.planeta
        ORDER BY id_api;

        /* ---------- dim_personagem: API + extras da curadoria */
        INSERT INTO dw.dim_personagem (id_api, codigo_extra, nome, raca, genero, afiliacao, sk_planeta, url_imagem,
                                       ki_api_valor, ki_api_status, ki_max_api_valor, ki_max_api_status, origem)
        SELECT p.id_api, NULL, p.nome, p.raca, p.genero, p.afiliacao, pl.sk_planeta, p.url_imagem,
               p.ki_valor, p.ki_status, p.ki_max_valor, p.ki_max_status, 'api'
        FROM stg.personagem p
        LEFT JOIN dw.dim_planeta pl ON pl.id_api = p.id_planeta_origem
        ORDER BY p.id_api;

        INSERT INTO dw.dim_personagem (id_api, codigo_extra, nome, raca, genero, afiliacao, sk_planeta, url_imagem,
                                       ki_api_valor, ki_api_status, ki_max_api_valor, ki_max_api_status, origem)
        SELECT NULL, e.codigo_extra, e.nome, e.raca, e.genero, e.afiliacao, NULL, NULL,
               NULL, 'desconhecido', NULL, 'desconhecido', 'curadoria'
        FROM stg.cur_personagem_extra e
        ORDER BY e.codigo_extra;

        /* ---------- dim_saga */
        INSERT INTO dw.dim_saga (codigo_saga, nome, serie, arco, ordem_cronologica, episodio_inicio, episodio_fim, filler)
        SELECT codigo_saga, nome, serie, arco, ordem_cronologica, episodio_inicio, episodio_fim, filler
        FROM stg.cur_saga
        ORDER BY ordem_cronologica;

        /* ---------- dim_transformacao
           1) formas usadas na curadoria (com dados da API quando há id)
           2) transformações da API que a curadoria não usa (catálogo completo) */
        ;WITH formas_cur AS (
            SELECT dp.sk_personagem, c.forma, MAX(c.id_transformacao_api) AS id_api
            FROM stg.cur_poder c
            JOIN dw.dim_personagem dp
              ON (c.id_personagem_api IS NOT NULL AND dp.id_api = c.id_personagem_api)
              OR (c.id_personagem_api IS NULL AND dp.codigo_extra = c.codigo_extra)
            GROUP BY dp.sk_personagem, c.forma
        ),
        todas AS (
            SELECT f.sk_personagem, f.forma, f.id_api, 'curadoria' AS origem
            FROM formas_cur f
            UNION ALL
            SELECT dp.sk_personagem, t.nome, t.id_api, 'api'
            FROM stg.personagem_transformacao pt
            JOIN stg.transformacao t   ON t.id_api = pt.id_transformacao_api
            JOIN dw.dim_personagem dp  ON dp.id_api = pt.id_personagem_api
            WHERE NOT EXISTS (SELECT 1 FROM formas_cur f WHERE f.id_api = pt.id_transformacao_api)
        )
        INSERT INTO dw.dim_transformacao (sk_personagem, forma, e_base, ordem, id_api, nome_api, ki_api_valor, url_imagem, origem)
        SELECT a.sk_personagem, a.forma,
               CASE WHEN a.forma = N'Base' THEN 1 ELSE 0 END,
               CASE WHEN a.forma = N'Base' THEN 0 ELSE COALESCE(pt.ordem, 90) END,
               a.id_api, t.nome, t.ki_valor, t.url_imagem, a.origem
        FROM todas a
        LEFT JOIN stg.transformacao t ON t.id_api = a.id_api
        LEFT JOIN stg.personagem_transformacao pt ON pt.id_transformacao_api = a.id_api
        ORDER BY a.sk_personagem, CASE WHEN a.forma = N'Base' THEN 0 ELSE COALESCE(pt.ordem, 90) END, a.forma;

        /* ---------- fato_poder */
        INSERT INTO dw.fato_poder (sk_personagem, sk_saga, sk_transformacao, nivel_poder, nivel_poder_log10,
                                   fonte_valor, referencia, observacao)
        SELECT dp.sk_personagem, ds.sk_saga, dt.sk_transformacao, c.nivel_poder,
               CASE WHEN c.nivel_poder > 0 THEN LOG10(CAST(c.nivel_poder AS FLOAT)) END,
               c.fonte_valor, c.referencia, c.observacao
        FROM stg.cur_poder c
        JOIN dw.dim_personagem dp
          ON (c.id_personagem_api IS NOT NULL AND dp.id_api = c.id_personagem_api)
          OR (c.id_personagem_api IS NULL AND dp.codigo_extra = c.codigo_extra)
        JOIN dw.dim_saga ds          ON ds.codigo_saga = c.codigo_saga
        JOIN dw.dim_transformacao dt ON dt.sk_personagem = dp.sk_personagem AND dt.forma = c.forma;

        /* ---------- fato_luta (poder de cada lado vem da fato_poder) */
        INSERT INTO dw.fato_luta (id_luta, sk_saga, sk_vencedor, sk_transformacao_vencedor, sk_perdedor,
                                  sk_transformacao_perdedor, resultado, poder_vencedor, poder_perdedor, zebra,
                                  episodio, observacao)
        SELECT l.id_luta, ds.sk_saga,
               v.sk_personagem, tv.sk_transformacao,
               p.sk_personagem, tp.sk_transformacao,
               l.resultado, fv.nivel_poder, fp.nivel_poder,
               CASE WHEN l.resultado = 'vitoria' AND fv.nivel_poder < fp.nivel_poder THEN 1 ELSE 0 END,
               l.episodio, l.observacao
        FROM stg.cur_luta l
        JOIN dw.dim_saga ds ON ds.codigo_saga = l.codigo_saga
        JOIN dw.dim_personagem v
          ON (l.vencedor_id_api IS NOT NULL AND v.id_api = l.vencedor_id_api)
          OR (l.vencedor_id_api IS NULL AND v.codigo_extra = l.vencedor_codigo_extra)
        JOIN dw.dim_personagem p
          ON (l.perdedor_id_api IS NOT NULL AND p.id_api = l.perdedor_id_api)
          OR (l.perdedor_id_api IS NULL AND p.codigo_extra = l.perdedor_codigo_extra)
        JOIN dw.dim_transformacao tv ON tv.sk_personagem = v.sk_personagem AND tv.forma = l.forma_vencedor
        JOIN dw.dim_transformacao tp ON tp.sk_personagem = p.sk_personagem AND tp.forma = l.forma_perdedor
        LEFT JOIN dw.fato_poder fv ON fv.sk_personagem = v.sk_personagem AND fv.sk_saga = ds.sk_saga
                                  AND fv.sk_transformacao = tv.sk_transformacao
        LEFT JOIN dw.fato_poder fp ON fp.sk_personagem = p.sk_personagem AND fp.sk_saga = ds.sk_saga
                                  AND fp.sk_transformacao = tp.sk_transformacao;

        /* ---------- testes DEPOIS: nada pode ter ficado para trás */
        IF (SELECT COUNT(*) FROM dw.fato_poder) <> (SELECT COUNT(*) FROM stg.cur_poder)
            THROW 50003, N'fato_poder: linhas da curadoria não encontraram dimensão (join perdeu linhas)', 1;
        IF (SELECT COUNT(*) FROM dw.fato_luta) <> (SELECT COUNT(*) FROM stg.cur_luta)
            THROW 50004, N'fato_luta: linhas da curadoria não encontraram dimensão (join perdeu linhas)', 1;
        IF EXISTS (SELECT 1 FROM dw.fato_luta WHERE poder_vencedor IS NULL OR poder_perdedor IS NULL)
            THROW 50005, N'fato_luta: luta sem nível de poder de um dos lados', 1;
        IF EXISTS (SELECT sk_personagem, forma FROM dw.dim_transformacao GROUP BY sk_personagem, forma HAVING COUNT(*) > 1)
            THROW 50006, N'dim_transformacao: forma duplicada para o mesmo personagem', 1;

        COMMIT;

        SELECT @linhas = (SELECT COUNT(*) FROM dw.dim_planeta) + (SELECT COUNT(*) FROM dw.dim_personagem)
                       + (SELECT COUNT(*) FROM dw.dim_saga) + (SELECT COUNT(*) FROM dw.dim_transformacao)
                       + (SELECT COUNT(*) FROM dw.fato_poder) + (SELECT COUNT(*) FROM dw.fato_luta);
        EXEC ctl.sp_log @etapa = @etapa, @status = 'SUCESSO', @linhas_afetadas = @linhas,
                        @mensagem = N'ok', @id_execucao = @id;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        SET @msg = ERROR_MESSAGE();
        EXEC ctl.sp_log @etapa = @etapa, @status = 'ERRO', @mensagem = @msg, @id_execucao = @id;
        THROW;
    END CATCH
END
GO

/* ----------------------------------------------------- conferência */
CREATE OR ALTER VIEW dw.vw_resumo_carga
AS
SELECT 'dim_planeta' AS tabela, COUNT(*) AS linhas FROM dw.dim_planeta
UNION ALL SELECT 'dim_personagem', COUNT(*) FROM dw.dim_personagem
UNION ALL SELECT 'dim_saga', COUNT(*) FROM dw.dim_saga
UNION ALL SELECT 'dim_transformacao', COUNT(*) FROM dw.dim_transformacao
UNION ALL SELECT 'fato_poder', COUNT(*) FROM dw.fato_poder
UNION ALL SELECT 'fato_luta', COUNT(*) FROM dw.fato_luta;
GO

/* Mais forte de cada saga — prévia da página "Linha do tempo" */
CREATE OR ALTER VIEW dw.vw_mais_forte_por_saga
AS
SELECT ordem_cronologica, saga, personagem, forma, nivel_poder
FROM (
    SELECT s.ordem_cronologica, s.nome AS saga, p.nome AS personagem, t.forma, f.nivel_poder,
           ROW_NUMBER() OVER (PARTITION BY s.sk_saga ORDER BY f.nivel_poder DESC) AS rn
    FROM dw.fato_poder f
    JOIN dw.dim_saga s          ON s.sk_saga = f.sk_saga
    JOIN dw.dim_personagem p    ON p.sk_personagem = f.sk_personagem
    JOIN dw.dim_transformacao t ON t.sk_transformacao = f.sk_transformacao
) x
WHERE rn = 1;
GO
