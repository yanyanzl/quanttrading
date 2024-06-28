-- /* and end with */
/* capital or lower case sensitive to the names */ 

create database ai1;
revoke all on database ai1 from public;


create role aiwrite;
GRANT connect on database ai1 to aiwrite;

GRANT USAGE, CREATE ON SCHEMA public TO aiwrite;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO aiwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aiwrite;

GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO aiwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO aiwrite;

create user aiapp with password '080802';

grant aiwrite to aiapp;

CREATE ROLE airead;
GRANT connect on database ai1 to airead;
GRANT USAGE ON SCHEMA public TO airead;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO airead;
ALTER DEFAULT PRIVILEGES in SCHEMA public GRANT SELECT ON TABLES TO airead;