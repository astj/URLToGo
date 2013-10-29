URLToGo
=======
A simple private bookmarking web-app.

## Setup

### submodule

This repo uses a submodule `p5-Teng-Schema-Declare-Columns-DateTime`.

To setup submodules, do following commands:
```
$ git submodule init
$ git submodule update
$ cd modules/p5-Teng-Schema-Declare-Columns-DateTime
$ git checkout master
```
*Note*:
This repo's submodule `p5-Teng-Schema-Declare-Columns-DateTime` is linked to
[my folk](https://github.com/astj/p5-Teng-Schema-Declare-Columns-DateTime), not to [original version](https://github.com/shibayu36/p5-Teng-Schema-Declare-Columns-DateTime).
But that folk is currently identical with original version...

### DB config

You need to write DB settings in `config/***.conf`.
See a sample file at `config/development.conf.sample`.

## Deploy

This repo has been deployed on heroku, using [heroku-buildpack](https://github.com/akiym/heroku-buildpack-perl/tree/carton).

To install dependencies, use `carton install`.

## License

MIT
