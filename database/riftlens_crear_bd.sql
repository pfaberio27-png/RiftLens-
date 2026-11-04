/* ============================================================
   RiftLens - Base de datos RiftLensDB (SQL Server)

   Script único e idempotente:
     - En una PC sin la base: crea RiftLensDB y sus tablas.
     - En una PC con la base ya creada: agrega solo lo que
       falte (columnas, restricción e índices).
   Se puede ejecutar varias veces. No borra ni modifica filas.

   Debe coincidir con los modelos de SQLAlchemy en
   backend/app/models/.
   ============================================================ */

SET NOCOUNT ON;
GO

IF DB_ID(N'RiftLensDB') IS NULL
BEGIN
    CREATE DATABASE RiftLensDB;
    PRINT 'Base de datos RiftLensDB creada.';
END
GO

USE RiftLensDB;
GO


/* ============================================================
   1. TABLAS (solo si no existen)
   ============================================================ */

IF OBJECT_ID(N'dbo.Jugadores', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Jugadores (
        jugador_id                  INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_Jugadores PRIMARY KEY,
        puuid                       VARCHAR(100)      NOT NULL
            CONSTRAINT UQ_Jugadores_puuid UNIQUE,
        riot_name                   VARCHAR(100)      NOT NULL,
        tag_line                    VARCHAR(30)       NOT NULL,
        region                      VARCHAR(20)       NOT NULL,
        fecha_registro              DATETIME          NOT NULL
            CONSTRAINT DF_Jugadores_fecha_registro DEFAULT GETDATE(),
        fecha_ultima_actualizacion  DATETIME          NOT NULL
            CONSTRAINT DF_Jugadores_fecha_ultima_actualizacion DEFAULT GETDATE()
    );
    PRINT 'Tabla Jugadores creada.';
END
GO

IF OBJECT_ID(N'dbo.Partidas', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Partidas (
        partida_id          INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_Partidas PRIMARY KEY,
        match_id            VARCHAR(50)       NOT NULL
            CONSTRAINT UQ_Partidas_match_id UNIQUE,
        queue_id            INT               NULL,
        modo                VARCHAR(50)       NULL,
        duracion_segundos   INT               NULL,
        fecha_partida       DATETIME          NULL,
        fecha_registro      DATETIME          NOT NULL
            CONSTRAINT DF_Partidas_fecha_registro DEFAULT GETDATE(),
        es_remake           BIT               NOT NULL
            CONSTRAINT DF_Partidas_es_remake DEFAULT 0,
        version_parche      VARCHAR(20)       NULL,
        equipos_json        NVARCHAR(MAX)     NULL
    );
    PRINT 'Tabla Partidas creada.';
END
GO

IF OBJECT_ID(N'dbo.EstadisticasPartida', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EstadisticasPartida (
        estadistica_id      INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_EstadisticasPartida PRIMARY KEY,
        jugador_id          INT               NOT NULL
            CONSTRAINT FK_Estadisticas_Jugadores
            REFERENCES dbo.Jugadores (jugador_id),
        partida_id          INT               NOT NULL
            CONSTRAINT FK_Estadisticas_Partidas
            REFERENCES dbo.Partidas (partida_id),
        campeon             VARCHAR(100)      NULL,
        rol                 VARCHAR(30)       NULL,
        victoria            BIT               NOT NULL,
        kills               INT               NOT NULL
            CONSTRAINT DF_Estadisticas_kills DEFAULT 0,
        deaths              INT               NOT NULL
            CONSTRAINT DF_Estadisticas_deaths DEFAULT 0,
        assists             INT               NOT NULL
            CONSTRAINT DF_Estadisticas_assists DEFAULT 0,
        kda                 DECIMAL(10, 2)    NOT NULL
            CONSTRAINT DF_Estadisticas_kda DEFAULT 0,
        cs                  INT               NOT NULL
            CONSTRAINT DF_Estadisticas_cs DEFAULT 0,
        cs_por_minuto       DECIMAL(10, 2)    NOT NULL
            CONSTRAINT DF_Estadisticas_cs_por_minuto DEFAULT 0,
        oro                 INT               NOT NULL
            CONSTRAINT DF_Estadisticas_oro DEFAULT 0,
        oro_por_minuto      DECIMAL(10, 2)    NOT NULL
            CONSTRAINT DF_Estadisticas_oro_por_minuto DEFAULT 0,
        [daño_campeones]    INT               NOT NULL
            CONSTRAINT DF_Estadisticas_dano_campeones DEFAULT 0,
        [daño_por_minuto]   DECIMAL(12, 2)    NOT NULL
            CONSTRAINT DF_Estadisticas_dano_por_minuto DEFAULT 0,
        vision_score        INT               NOT NULL
            CONSTRAINT DF_Estadisticas_vision_score DEFAULT 0,
        fecha_registro      DATETIME          NOT NULL
            CONSTRAINT DF_Estadisticas_fecha_registro DEFAULT GETDATE(),
        datos_json          NVARCHAR(MAX)     NULL,
        CONSTRAINT UQ_Estadistica_Jugador_Partida
            UNIQUE (jugador_id, partida_id)
    );
    PRINT 'Tabla EstadisticasPartida creada.';
END
GO


/* ============================================================
   2. COLUMNAS NUEVAS (bases creadas con una versión anterior)
   ============================================================ */

IF COL_LENGTH(N'dbo.Partidas', N'es_remake') IS NULL
BEGIN
    ALTER TABLE dbo.Partidas
        ADD es_remake BIT NOT NULL
            CONSTRAINT DF_Partidas_es_remake DEFAULT 0;
    PRINT 'Columna Partidas.es_remake agregada.';
END
GO

IF COL_LENGTH(N'dbo.Partidas', N'version_parche') IS NULL
BEGIN
    ALTER TABLE dbo.Partidas
        ADD version_parche VARCHAR(20) NULL;
    PRINT 'Columna Partidas.version_parche agregada.';
END
GO

IF COL_LENGTH(N'dbo.Partidas', N'equipos_json') IS NULL
BEGIN
    ALTER TABLE dbo.Partidas
        ADD equipos_json NVARCHAR(MAX) NULL;
    PRINT 'Columna Partidas.equipos_json agregada.';
END
GO

IF COL_LENGTH(N'dbo.EstadisticasPartida', N'datos_json') IS NULL
BEGIN
    ALTER TABLE dbo.EstadisticasPartida
        ADD datos_json NVARCHAR(MAX) NULL;
    PRINT 'Columna EstadisticasPartida.datos_json agregada.';
END
GO


/* ============================================================
   3. RESTRICCIÓN UNIQUE (jugador_id, partida_id)
   Si ya hay filas repetidas NO se crea ni se borra nada:
   se muestran las repetidas para revisarlas a mano.
   ============================================================ */

IF NOT EXISTS (
    SELECT 1
    FROM sys.objects
    WHERE name = N'UQ_Estadistica_Jugador_Partida'
      AND parent_object_id = OBJECT_ID(N'dbo.EstadisticasPartida')
)
BEGIN
    IF EXISTS (
        SELECT jugador_id, partida_id
        FROM dbo.EstadisticasPartida
        GROUP BY jugador_id, partida_id
        HAVING COUNT(*) > 1
    )
    BEGIN
        PRINT 'AVISO: hay estadísticas repetidas por (jugador_id, partida_id).';
        PRINT 'No se creó UQ_Estadistica_Jugador_Partida. Revisa estas filas:';

        SELECT jugador_id, partida_id, COUNT(*) AS repeticiones
        FROM dbo.EstadisticasPartida
        GROUP BY jugador_id, partida_id
        HAVING COUNT(*) > 1;
    END
    ELSE
    BEGIN
        ALTER TABLE dbo.EstadisticasPartida
            ADD CONSTRAINT UQ_Estadistica_Jugador_Partida
            UNIQUE (jugador_id, partida_id);
        PRINT 'Restricción UQ_Estadistica_Jugador_Partida creada.';
    END
END
GO


/* ============================================================
   4. ÍNDICES
   ============================================================ */

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_Partidas_fecha'
      AND object_id = OBJECT_ID(N'dbo.Partidas')
)
BEGIN
    CREATE INDEX IX_Partidas_fecha
        ON dbo.Partidas (fecha_partida);
    PRINT 'Índice IX_Partidas_fecha creado.';
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_Estadisticas_jugador'
      AND object_id = OBJECT_ID(N'dbo.EstadisticasPartida')
)
BEGIN
    CREATE INDEX IX_Estadisticas_jugador
        ON dbo.EstadisticasPartida (jugador_id);
    PRINT 'Índice IX_Estadisticas_jugador creado.';
END
GO

PRINT 'RiftLensDB lista.';
GO
