/* =====================================================================
   Scouter BI — 01_stg_tables.sql
   Tabelas de staging: espelho tratado minimamente da API.
   ki_texto guarda o valor cru; ki_valor guarda o número convertido
   em Python (DECIMAL(38,0), pois 90 Septillion = 9e25 estoura BIGINT).
   Cada carga substitui o conteúdo (TRUNCATE + INSERT) e grava id_execucao.
   ===================================================================== */
USE DBZ_BI;
GO

IF OBJECT_ID(N'stg.planeta', N'U') IS NULL
CREATE TABLE stg.planeta (
    id_api        INT            NOT NULL CONSTRAINT PK_stg_planeta PRIMARY KEY,
    nome          NVARCHAR(100)  NOT NULL,
    destruido     BIT            NULL,
    descricao     NVARCHAR(MAX)  NULL,
    url_imagem    NVARCHAR(400)  NULL,
    deleted_at    DATETIME2(0)   NULL,
    id_execucao   INT            NOT NULL,
    dt_carga      DATETIME2(0)   NOT NULL CONSTRAINT DF_stg_planeta_dt DEFAULT SYSDATETIME()
);
GO

IF OBJECT_ID(N'stg.personagem', N'U') IS NULL
CREATE TABLE stg.personagem (
    id_api            INT            NOT NULL CONSTRAINT PK_stg_personagem PRIMARY KEY,
    nome              NVARCHAR(100)  NOT NULL,
    raca              NVARCHAR(50)   NULL,
    genero            NVARCHAR(20)   NULL,
    afiliacao         NVARCHAR(60)   NULL,
    ki_texto          NVARCHAR(60)   NULL,
    ki_valor          DECIMAL(38,0)  NULL,
    ki_max_texto      NVARCHAR(60)   NULL,
    ki_max_valor      DECIMAL(38,0)  NULL,
    id_planeta_origem INT            NULL,
    descricao         NVARCHAR(MAX)  NULL,
    url_imagem        NVARCHAR(400)  NULL,
    deleted_at        DATETIME2(0)   NULL,
    id_execucao       INT            NOT NULL,
    dt_carga          DATETIME2(0)   NOT NULL CONSTRAINT DF_stg_personagem_dt DEFAULT SYSDATETIME()
);
GO

IF OBJECT_ID(N'stg.transformacao', N'U') IS NULL
CREATE TABLE stg.transformacao (
    id_api        INT            NOT NULL CONSTRAINT PK_stg_transformacao PRIMARY KEY,
    nome          NVARCHAR(100)  NOT NULL,
    ki_texto      NVARCHAR(60)   NULL,
    ki_valor      DECIMAL(38,0)  NULL,
    url_imagem    NVARCHAR(400)  NULL,
    deleted_at    DATETIME2(0)   NULL,
    id_execucao   INT            NOT NULL,
    dt_carga      DATETIME2(0)   NOT NULL CONSTRAINT DF_stg_transformacao_dt DEFAULT SYSDATETIME()
);
GO

/* Ponte: só o detalhe /characters/{id} diz a qual personagem cada forma pertence */
IF OBJECT_ID(N'stg.personagem_transformacao', N'U') IS NULL
CREATE TABLE stg.personagem_transformacao (
    id_personagem_api     INT NOT NULL,
    id_transformacao_api  INT NOT NULL,
    ordem                 SMALLINT NOT NULL,   -- posição na lista da API
    id_execucao           INT NOT NULL,
    dt_carga              DATETIME2(0) NOT NULL CONSTRAINT DF_stg_pt_dt DEFAULT SYSDATETIME(),
    CONSTRAINT PK_stg_personagem_transformacao PRIMARY KEY (id_personagem_api, id_transformacao_api)
);
GO

/* Status do ki (numerico | desconhecido | incomensuravel | invalido).
   ALTER idempotente: funciona em bancos criados antes desta coluna existir. */
IF COL_LENGTH(N'stg.personagem', N'ki_status') IS NULL
    ALTER TABLE stg.personagem ADD ki_status VARCHAR(20) NULL;
IF COL_LENGTH(N'stg.personagem', N'ki_max_status') IS NULL
    ALTER TABLE stg.personagem ADD ki_max_status VARCHAR(20) NULL;
IF COL_LENGTH(N'stg.transformacao', N'ki_status') IS NULL
    ALTER TABLE stg.transformacao ADD ki_status VARCHAR(20) NULL;
GO

/* Conferência pós-carga: só 'invalido' é problema; os demais status são esperados */
CREATE OR ALTER VIEW stg.vw_qualidade_carga
AS
SELECT 'personagem' AS tabela, COUNT(*) AS linhas,
       SUM(CASE WHEN ki_status = 'invalido' THEN 1 ELSE 0 END)
     + SUM(CASE WHEN ki_max_status = 'invalido' THEN 1 ELSE 0 END) AS ki_invalido,
       SUM(CASE WHEN ki_max_status = 'desconhecido' THEN 1 ELSE 0 END)   AS ki_desconhecido,
       SUM(CASE WHEN ki_max_status = 'incomensuravel' THEN 1 ELSE 0 END) AS ki_incomensuravel
FROM stg.personagem
UNION ALL
SELECT 'transformacao', COUNT(*),
       SUM(CASE WHEN ki_status = 'invalido' THEN 1 ELSE 0 END),
       SUM(CASE WHEN ki_status = 'desconhecido' THEN 1 ELSE 0 END),
       SUM(CASE WHEN ki_status = 'incomensuravel' THEN 1 ELSE 0 END)
FROM stg.transformacao
UNION ALL
SELECT 'planeta', COUNT(*), 0, 0, 0 FROM stg.planeta
UNION ALL
SELECT 'personagem_transformacao', COUNT(*), 0, 0, 0 FROM stg.personagem_transformacao;
GO
