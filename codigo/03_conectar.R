library(RPostgres)
con_aiven <- dbConnect(RPostgres::Postgres(), sslmode="verify-full")