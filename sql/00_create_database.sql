/* =====================================================================
   Scouter BI — 00_create_database.sql
   Cria o banco DBZ_BI, os schemas e a tabela de log de execução.
   Idempotente: pode rodar mais de uma vez.
   Execução: sqlcmd -S localhost -E -i sql\00_create_database.sql
   ===================================================================== */

IF DB_ID(N'DBZ_BI') IS NULL
BEGIN
    CREATE DATABASE DBZ_BI;
END
GO

ALTER DATABASE DBZ_BI SET RECOVERY SIMPLE;
GO

USE DBZ_BI;
GO

/* stg = dado cru da API e dos CSVs | dw = modelo estrela | ctl = controle */
IF SCHEMA_ID(N'stg') IS NULL EXEC (N'CREATE SCHEMA stg AUTHORIZATION dbo;');
IF SCHEMA_ID(N'dw')  IS NULL EXEC (N'CREATE SCHEMA dw  AUTHORIZATION dbo;');
IF SCHEMA_ID(N'ctl') IS NULL EXEC (N'CREATE SCHEMA ctl AUTHORIZATION dbo;');
GO

/* Log de cada execução do pipeline (extração, carga, procedures) */
IF OBJECT_ID(N'ctl.log_execucao', N'U') IS NULL
BEGIN
    CREATE TABLE ctl.log_execucao (
        id_execucao     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_log_execucao PRIMARY KEY,
        etapa           VARCHAR(100)  NOT NULL,   -- ex.: extracao_characters, sp_carga_dim_personagem
        status          VARCHAR(20)   NOT NULL,   -- INICIADO | SUCESSO | ERRO
        linhas_afetadas INT           NULL,
        mensagem        NVARCHAR(4000) NULL,
        dt_inicio       DATETIME2(0)  NOT NULL CONSTRAINT DF_log_dt_inicio DEFAULT SYSDATETIME(),
        dt_fim          DATETIME2(0)  NULL,
        duracao_seg AS DATEDIFF(SECOND, dt_inicio, dt_fim)
    );
END
GO

/* Procedure padrão para registrar o log */
CREATE OR ALTER PROCEDURE ctl.sp_log
    @etapa           VARCHAR(100),
    @status          VARCHAR(20),
    @linhas_afetadas INT = NULL,
    @mensagem        NVARCHAR(4000) = NULL,
    @id_execucao     INT = NULL OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    IF @id_execucao IS NULL
    BEGIN
        INSERT INTO ctl.log_execucao (etapa, status, linhas_afetadas, mensagem)
        VALUES (@etapa, @status, @linhas_afetadas, @mensagem);
        SET @id_execucao = SCOPE_IDENTITY();
    END
    ELSE
    BEGIN
        UPDATE ctl.log_execucao
           SET status          = @status,
               linhas_afetadas = @linhas_afetadas,
               mensagem        = @mensagem,
               dt_fim          = SYSDATETIME()
         WHERE id_execucao = @id_execucao;
    END
END
GO

/* Teste rápido */
DECLARE @id INT;
EXEC ctl.sp_log @etapa = 'fase0_setup', @status = 'INICIADO', @id_execucao = @id OUTPUT;
EXEC ctl.sp_log @etapa = 'fase0_setup', @status = 'SUCESSO', @linhas_afetadas = 0,
                @mensagem = N'Banco e schemas criados', @id_execucao = @id;

SELECT name AS schema_criado FROM sys.schemas WHERE name IN ('stg','dw','ctl');
SELECT TOP 1 * FROM ctl.log_execucao ORDER BY id_execucao DESC;
GO
