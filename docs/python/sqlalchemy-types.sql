-- Mögliche Typen am Beispiel der Lab-Tabelle
-- ------------------------------------------
--
-- https://docs.sqlalchemy.org/en/13/core/type_basics.html#vendor-specific-types
--
-- Zahlen:
-- - BigInteger
-- - Integer 		INT
-- - SmallInteger
-- - Float 		    floating point values
--
-- Ja/Nein:
-- - Boolean 		BOOLEAN, INT, TINYINT depending on db support for boolean type
--
-- Text:
-- - String 		ASCII strings, VARCHAR
-- - Unicode 		Unicode string - VARCHAR or NVARCHAR depending on database
-- - Text
-- - UnicodeText
--
-- Datum und Zeit:
-- - DateTime 		DATETIME or TIMESTAMP returns Python datetime() objects
-- - Date
-- - Time

-- Create Statement
-- ----------------

-- SQLite 3.27.2  (Version ermittelt via select sqlite_version();)

CREATE TABLE lab (
	id INTEGER NOT NULL,
  -- id BIGINT NOT NULL,
	bigint1 BIGINT,
	int1 INTEGER,
	smallint1 SMALLINT,
	float1 FLOAT,
	bool1 BOOLEAN,
	string1 VARCHAR(255),
	text1 TEXT,
	datetime1 DATETIME,
	date1 DATE,
	time1 TIME,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id),
	CHECK (bool1 IN (0, 1))
);


-- MySQL (10.4.11-MariaDB über PyMySQL 0.9.3)

CREATE TABLE `lab` (
  `id` int(11) NOT NULL,
  `bigint1` bigint(20) DEFAULT NULL,
  `int1` int(11) DEFAULT NULL,
  `smallint1` smallint(6) DEFAULT NULL,
  `float1` float DEFAULT NULL,
  `bool1` tinyint(1) DEFAULT NULL,
  `string1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `text1` text COLLATE utf8_unicode_ci DEFAULT NULL,
  `datetime1` datetime DEFAULT NULL,
  `date1` date DEFAULT NULL,
  `time1` time DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ;

ALTER TABLE `lab`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `lab`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;


-- MS SQL Server 2017

CREATE TABLE [dbo].[lab](
    [id] [int] IDENTITY(1,1) NOT NULL,
    [bigint1] [bigint] NULL,
    [int1] [int] NULL,
    [smallint1] [smallint] NULL,
    [float1] [float] NULL,
    [bool1] [bit] NULL,
    [string1] [varchar](255) NULL,
    [text1] [varchar](max) NULL,
    [datetime1] [datetime] NULL,
    [date1] [date] NULL,
    [time1] [time](7) NULL,
    [created_at] [datetime] NULL,
    [updated_at] [datetime] NULL,
  PRIMARY KEY CLUSTERED ( [id] ASC ) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
  ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
