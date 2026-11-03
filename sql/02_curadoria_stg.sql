/* =====================================================================
   Scouter BI — 02_curadoria_stg.sql
   Staging dos CSVs de curadoria (pasta data/curadoria, arquivos .csv).
   Carregados por src/load_curadoria.py (TRUNCATE + INSERT).
   ===================================================================== */
USE DBZ_BI;
GO

IF OBJECT_ID(N'stg.cur_saga', N'U') IS NULL
CREATE TABLE stg.cur_saga (
    codigo_saga        VARCHAR(30)   NOT NULL CONSTRAINT PK_stg_cur_saga PRIMARY KEY,
    nome               NVARCHAR(80)  NOT NULL,
    serie              VARCHAR(10)   NOT NULL,
    arco               NVARCHAR(40)  NOT NULL,
    ordem_cronologica  SMALLINT      NOT NULL,
    episodio_inicio    SMALLINT      NULL,
    episodio_fim       SMALLINT      NULL,
    filler             BIT           NOT NULL,
    id_execucao        INT           NOT NULL,
    dt_carga           DATETIME2(0)  NOT NULL CONSTRAINT DF_stg_cur_saga_dt DEFAULT SYSDATETIME()
);
GO

IF OBJECT_ID(N'stg.cur_personagem_extra', N'U') IS NULL
CREATE TABLE stg.cur_personagem_extra (
    codigo_extra   VARCHAR(40)   NOT NULL CONSTRAINT PK_stg_cur_personagem_extra PRIMARY KEY,
    nome           NVARCHAR(100) NOT NULL,
    raca           NVARCHAR(50)  NULL,
    genero         NVARCHAR(20)  NULL,
    afiliacao      NVARCHAR(60)  NULL,
    id_execucao    INT           NOT NULL,
    dt_carga       DATETIME2(0)  NOT NULL CONSTRAINT DF_stg_cur_pe_dt DEFAULT SYSDATETIME()
);
GO

IF OBJECT_ID(N'stg.cur_poder', N'U') IS NULL
CREATE TABLE stg.cur_poder (
    linha_csv             INT            NOT NULL CONSTRAINT PK_stg_cur_poder PRIMARY KEY,
    id_personagem_api     INT            NULL,
    codigo_extra          VARCHAR(40)    NULL,
    personagem            NVARCHAR(100)  NOT NULL,
    codigo_saga           VARCHAR(30)    NOT NULL,
    forma                 NVARCHAR(60)   NOT NULL,
    id_transformacao_api  INT            NULL,
    nivel_poder           DECIMAL(38,0)  NOT NULL,
    fonte_valor           VARCHAR(20)    NOT NULL,
    referencia            NVARCHAR(200)  NULL,
    observacao            NVARCHAR(300)  NULL,
    id_execucao           INT            NOT NULL,
    dt_carga              DATETIME2(0)   NOT NULL CONSTRAINT DF_stg_cur_poder_dt DEFAULT SYSDATETIME()
);
GO

IF OBJECT_ID(N'stg.cur_luta', N'U') IS NULL
CREATE TABLE stg.cur_luta (
    id_luta                INT           NOT NULL CONSTRAINT PK_stg_cur_luta PRIMARY KEY,
    codigo_saga            VARCHAR(30)   NOT NULL,
    vencedor_id_api        INT           NULL,
    vencedor_codigo_extra  VARCHAR(40)   NULL,
    vencedor               NVARCHAR(100) NOT NULL,
    forma_vencedor         NVARCHAR(60)  NOT NULL,
    perdedor_id_api        INT           NULL,
    perdedor_codigo_extra  VARCHAR(40)   NULL,
    perdedor               NVARCHAR(100) NOT NULL,
    forma_perdedor         NVARCHAR(60)  NOT NULL,
    resultado              VARCHAR(20)   NOT NULL,
    episodio               SMALLINT      NULL,
    observacao             NVARCHAR(300) NULL,
    id_execucao            INT           NOT NULL,
    dt_carga               DATETIME2(0)  NOT NULL CONSTRAINT DF_stg_cur_luta_dt DEFAULT SYSDATETIME()
);
GO
