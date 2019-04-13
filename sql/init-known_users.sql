CREATE TABLE IF NOT EXISTS `known_users` (
	`ID`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	`ID_Inst`	INTEGER NOT NULL UNIQUE,
	`acct`	TEXT NOT NULL,
	`didMorning_at`	TEXT,
	`didSYou_at`	TEXT,
	`didWBack_at`	TEXT,
	`didGNight_at`	TEXT,
	`didUpdated_at`	TEXT,
	`didPassage_at` TEXT,
	`known_at`	TEXT
);