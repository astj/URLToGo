requires 'Teng';
requires 'Mojolicious';
requires 'Crypt::SaltedHash';
requires 'Net::DNS';
requires 'Email::Valid';
requires 'DateTime';
requires 'DBD::Pg';
requires 'DateTime::Format::Pg';

# modules
requires 'Exporter::Lite';
requires 'Class::Data::Inheritable';

on 'test' => sub {
    requires 'Test::More', '0.98';
    requires 'Test::Pretty';
    requires 'App::Prove::Plugin::Pretty';
}