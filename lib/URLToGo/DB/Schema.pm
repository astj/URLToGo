package URLToGo::DB::Schema;
use strict;
use warnings;
use Teng::Schema::Declare;
use Teng::Schema::Declare::Columns::DateTime;
use DateTime;
use DateTime::Format::Pg;

Teng::Schema::Declare::Columns::DateTime->format_class('DateTime::Format::Pg');

table {
    name 'users';
    pk 'id';
    columns qw (id username password email);
};

table {
    name 'bookmarks';
    pk 'id';
    columns qw (id url title owner_user_id visited_time entry_time comment);
    datetime_columns qw (visited_time entry_time);
};

1;
