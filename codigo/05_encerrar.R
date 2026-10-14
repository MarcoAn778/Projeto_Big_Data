dbDisconnect(con, shutdown=TRUE)
if (exists("con_aiven")) dbDisconnect(con_aiven)