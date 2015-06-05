create table if not exists plots (xtable TEXT NOT NULL, ytable TEXT NOT NULL, key INTEGER, name TEXT NOT NULL, callback_function TEXT DEFAULT "", PRIMARY KEY (xtable, ytable, key));

create table if not exists runs (run_num INTEGER NOT NULL, root_file TEXT, web_source TEXT, PRIMARY KEY(run_num, root_file));

create table if not exists TT_FE_STATUS_BITS (run_num, status TEXT, VALUE INTEGER, TT_id INTEGER );

create table if not exists TT_IDS (tt_id INTEGER PRIMARY KEY AUTOINCREMENT, TT INTEGER, Det TEXT, SM INTEGER);




