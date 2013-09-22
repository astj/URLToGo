package URLToGo::DB::Schema;
use strict;
use warnings;
use Teng::Schema::Declare;
use DateTime;

table {
    name 'users';
    pk 'id';
    columns qw (id username password email);
};

table {
    name 'bookmarks';
    pk 'id';
    columns qw (id url title owner_user_id visited_time entry_time comment;

};
1;
