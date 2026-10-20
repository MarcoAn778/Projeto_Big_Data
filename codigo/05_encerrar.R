if (exists("con_aiven") && DBI::dbIsValid(con_aiven)) DBI::dbDisconnect(con_aiven)
if (exists("con") && DBI::dbIsValid(con)) DBI::dbDisconnect(con, shutdown=TRUE)
