#!/usr/bin/env perl

require 5.10;

# Neccessary for Local test
#use lib '/opt/local/lib/perl5/vendor_perl/5.12.4';
#use lib '/opt/local/lib/perl5/site_perl/5.12.4';

use Mojolicious::Lite;
use Crypt::SaltedHash;

use utf8;

use lib './lib';
#Teng-DB
use URLToGo::DB;
# email Check
use Email::Valid;
# DateTime
use DateTime;

# Make cookie secure!
# というアピール
app->secret('Key of Encryption of Session Cookie');

my $db = URLToGo::DB->new({connect_info => ['dbi:Pg:dbname=ASTSimple;host=localhost','ast','itsme',{pg_enable_utf8=>1}]});
$db->load_plugin('Count');

#Helper to check whether authenticated or not
helper auth => sub {
    my $self = shift;

# Call another helper
    my $auth_result = $self->_auth_core;

# If auth succeeded -> Set session
# Prototypeより先ではきちんとセッションID作ってそれを預けた方がSecure
    if($auth_result)
    {
	$self->session({username => $self->stash->{username}, password => $self->stash->{password} });
    }

    return $auth_result;
};

#Helper to Insert to bookmarks
# $returned_hash = $self->add_bookmark({insert_params});
# 返り値
# { status=>(2|1|0), row=>(Teng::Row) }
# status=	2 : Succes
# 			1 : Already exists
#			0 : Other Error (Reserved)
helper add_bookmark => sub {
	my $self = shift;
	my $params_hash = shift;
	my $status;
#use Data::Dumper;
	my $itr = $db->search('bookmarks', {url => $params_hash->{url}, owner_user_id => $params_hash->{owner_user_id}});
	while(my $row = $itr->next)
	{
# 既に存在していた場合はそのrowを返す
		return +{ status=>1, row=>$row};
	}

	#引っかからなかったのでDBにInsertする
	my $row = $db->insert('bookmarks', $params_hash );
	return +{status=>2, row=>$row};



};

#Helper 
helper _auth_core => sub {
    my $self = shift;

# Sessionに入ってればそっちを使う
    my $username = $self->session->{username} // $self->param('username');
    my $password = $self->session->{password} // $self-> param('password');

    if(!defined($username) ) { return undef; }

    my $itr = $db->search('users', {username => $username});
    while(my $row = $itr->next)
    {
	my $password_in_db = $row->password;

	if( Crypt::SaltedHash->validate($password_in_db, $password) )
	{
	    $self->stash->{id} = $row->id;
	    $self->stash->{username} = $username;
	    $self->stash->{password} = $password;
	    return 1;
	}
    }
# No match!
    return 0;

};



# Not have to authenticated section
get '/' => sub {
  my $self = shift;
  my $auth_result = $self->auth;

  if ($auth_result)
  { 

	my $limit_display = 10;

	my @bookmarks_visited = ();
	my @bookmarks_nonvisited = ();
	my $counter=0;
	my $exceeds_nonvisited=0;
	my $exceeds_visited=0;

	#bookmarkの取得
	#未訪問のほう
	my $itr = $db->search('bookmarks', { owner_user_id => $self->stash->{id}, visited_time => \'IS NULL'}, +{order_by => 'entry_time desc', limit => $limit_display + 1});
	while(my $row = $itr->next)
	{
		$counter++; if($counter>$limit_display) { $exceeds_nonvisited=1; last;}
		my $visited_time = defined($row->visited_time) ? DateTime->from_epoch(epoch=>$row->visited_time)->strftime('%Y/%m/%d %H:%M') : '';
		push(@bookmarks_nonvisited, +{id=>$row->id, url=>$row->url, title=>(length $row->title ? $row->title : '(No title)'), comment=>$row->comment});
	}

	$counter=0;
	#既訪問のほう
	$itr = $db->search('bookmarks', { owner_user_id => $self->stash->{id}, visited_time => \'IS NOT NULL'}, +{order_by => 'visited_time desc', limit => $limit_display + 1});
	while(my $row = $itr->next)
	{
		$counter++; if($counter>$limit_display) { $exceeds_visited=1; last;}
		my $visited_time = defined($row->visited_time) ? DateTime->from_epoch(epoch=>$row->visited_time)->strftime('%Y/%m/%d %H:%M') : '';
		push(@bookmarks_visited, +{id=>$row->id, url=>$row->url, title=>(length $row->title ? $row->title : '(No title)'), comment=>$row->comment, visited_time=>$visited_time});
	}


	$self->stash(bookmarks_nonvisited => [@bookmarks_nonvisited]);
	$self->stash(bookmarks_visited => [@bookmarks_visited]);
	$self->stash(exceeds_nonvisited => $exceeds_nonvisited);
	$self->stash(exceeds_visited => $exceeds_visited);
	$self->stash(disp_channel => $self->param('disp_channel')//0);

#	$self->render_text('hoge' .Dumper($self->stash->{bookmarks}));

	  $self->render('user_top'); 
  }
  else
  {
#      $self->stash->{message} = 'You neeed to Login';
      $self->render('index'); 
  }
};

any '/login' => sub {
    my $self = shift;
    my $action = $self->flash('action');
    my $login_try = $self->param('login_try');
    my $auth_result = $self->auth;

    # prevent from redirect loooooop
    $action = (defined $action && $action ne '/login')? $action : '/';

    #Success
    if($auth_result) { return $self->redirect_to($action); }

    #Failed...
    $self->flash(action=>$action);

    if($login_try) { $self->stash->{message} = 'Login failed.';}

    $self->render;
#    $self->render_text('Login section<br>You tried to access '.$self->flash('action'));
};

# 既にLogoutしていてもLogoutは叩けるようにしておく
get '/logout' => sub {
    my $self = shift;

    # Delete session
    $self->session(expires => 1);
    # Usernameのstashも破棄する
    delete $self->stash->{username};

    $self->render;
};

any '/signup' => sub {
    my $self = shift;
    my $auth_result = $self->auth;

#Params
    my $username = $self->param('username');
    my $password = $self->param('password');
    my $email = $self->param('email');

    #認証済みならtopに追い払う
    if ($auth_result) { 
	$self->flash(message=>'You have already registered');
	$self->redirect_to('/');
    }

    # 引数の型検査
    # dbにアクセスしないで済む範囲から
    # 各変数ごとに確かめる
    my $error_occured = 0;
 
    if ( length($username) < 1 ) { $error_occured = 1; $self->stash->{signup_error_username} = 'You need User ID.'; } 
    elsif ( $username =~ /[^a-zA-Z0-9]/ ) { $error_occured = 1; $self->stash->{signup_error_username} = 'You can use only Alphabet and Numbers to User ID.'; }

    if ( length($password) < 6 ) { $error_occured = 1; $self->stash->{signup_error_password} = 'Password must be at least 6 characters.'; }
    elsif ( $password =~ /[^\x21-\x7e]/ ) { $error_occured = 1; $self->stash->{signup_error_password} = 'You can use only characters /w code \x21 .. \x7e .'; }

	# Verify email with Email::Valid
    if ( !defined (Email::Valid->address($email))) { $error_occured = 1; $self->stash->{signup_error_email} = 'You need to input a valid e-mail address.'; }

    NOERROR : if(!$error_occured)
    {
		# 型検査はOKなので既存とのカブりを調べる
		my $itr = $db->search('users', {username => $username});
		$itr->suppress_object_creation(1);
		while(my $rowhash = $itr->next)
		{
#ひっかかってもうた
		    $error_occured = 1;
		    $self->stash->{signup_error_username} = 'This User ID is already used by somebody.';
		    # ノンエラーのループから抜け出す
		    last NOERROR;
		}

	    # OK。
	    # PasswordをHash-nized する
		my $csh = Crypt::SaltedHash->new(algorithm => 'SHA-1');
		$csh->add($password);
	    # Generates Hash
		my $password_salted = $csh->generate;

	    # DBにInsertする
		my $row = $db->insert('users', +{username => $username, password=> $password_salted, email => $email});

		# Loginみたいなことをする
		my $auth_result = $self->auth;
		if ( $auth_result )
		{
			#login_succes
			# Redirect to welcome page
			$self->flash('message') = 'URLToGoへのユーザー登録が完了しました。';
			$self->redirect_to('welcome');
		}
		else
		{
			#Error
		}

	}

    $self->render;
};


# この下は認証してないとダメだからunderでハネる
under sub {
    my $self = shift;
    my $auth_result = $self->auth;

    #失敗したとき
    if (!$auth_result) {
	#行きたかったpathをここでKeepする
	#queryまでは保管しない
	#url_withにするとQueryまで保管できる。
	my $action_path = $self->url_with;
	$self->flash(action=>$action_path);

	#for dbg
	#$self->render_text("Path = ".$action_path."<br>".$self->url_with);
	$self->redirect_to('login');
	return 0;
    }

    return 1;
};


get '/welcome' => sub {
	my $self = shift;
	$self->render;
};

any '/add' => sub {
	my $self = shift;
	my $target_url=$self->param('url');
	my $target_title=$self->param('title')//'';

	# helperに投げて登録を確認する
	my $returned_hash = $self->add_bookmark(
	{owner_user_id=>$self->stash->{id}, url=>$target_url,title=>$target_title,entry_time => DateTime->now()->epoch }
	);

	$self->stash->{message} = ('Somehow Error', 'このページはもう登録してあります！', '登録しました！')[$returned_hash->{status}];

	if($returned_hash->{status} > 0 )
	{
		my $row = $returned_hash->{row};
	$self->stash->{bookmark_url} = $row->url;
	$self->stash->{bookmark_title} = $row->title;
	$self->stash->{bookmark_comment} = $row->comment;
	$self->stash->{bookmark_host} = Mojo::URL->new($self->stash->{bookmark_url})->host;
	$self->render;

	}
	else { $self->render('error_happens');}

};

get '/sp_bmlt' => sub {
	my $self = shift;

	$self->render();

};

get '/delete' => sub {
	my $self = shift;
	my $target_id = $self->param('to_id');

	# Get Entry's URL
	# 他人のEntryだったら(当然)消しちゃダメ
	my $itr = $db->search('bookmarks', { owner_user_id => $self->stash->{id}, id => $target_id});
	while(my $row = $itr->next)
	{
		$row->delete();
		$self->flash(message=>'削除しました！');
		return $self->redirect_to($self->param('cb_url'));
	}

	# ダメだった
	$self->render('error_happens', message=>'このURLではアクセスできません');


};

get '/jump' => sub {
	my $self = shift;
	my $target_id = $self->param('to_id');

	# Get Entry's URL
	# 他人のEntryだったら見えちゃだめ
	my $itr = $db->search('bookmarks', { owner_user_id => $self->stash->{id}, id => $target_id});
	while(my $row = $itr->next)
	{
		$row->update(+{visited_time => DateTime->now()->epoch});
		return $self->redirect_to($row->url);
	}

	# ダメだった
	$self->render('error_happens', message=>'このURLではアクセスできません');

};

app->start;
__DATA__


@@ index.html.ep
% layout 'default';
% title 'TOP';
<div class="hero-unit">
  <h1>URLToGo</h1>
  <p>PCで読みかけのページを登録、スマホで続きを読む</p>
</div>
<%= stash 'message' %>
<%= include 'partial_login_form', formId => 'main' %>

@@ login.html.ep
% layout 'default';
% title 'Login';
<h2>ログインする</h2>
<p> <%= stash 'message' %> </p>
<%= include 'partial_login_form', formId => 'main' %>


@@ logout.html.ep
% layout 'default';
% title 'Logout';
<h2>Logout</h2>
<p>You are now Logouted.</p>

@@ partial_add_bookmark.html.ep
<form action="<%= url_for('/add') %>" method="post" class="form-inline" id="AddBookmark">
    <input type="text" name="url" id="AddBookmarkUrl" placeholder="http://hatena.jp/" />
    <input type="submit" value="Add Bookmark" class="btn btn-primary" />
    <input type="hidden" name="login_try" value="1" />
    <input type="hidden" name="callback_url" value="<%= url_for %>" />
</form>

@@ user_top.html.ep
% layout 'default';
<p><%= flash 'message' %></p>
<p><%= stash 'message' %></p>
<div class="accordion" id="add_accordion">
  <div class="accordion-group">
    <div class="accordion-heading">
      <a class="accordion-toggle" data-toggle="collapse" data-parent="#add_accordion" href="#adac_collapseOne">
        PCで読みかけのページを持ち出すには？
      </a>
    </div>
    <div id="adac_collapseOne" class="accordion-body collapse">
      <div class="accordion-inner">
        <p>この→<a href="<%= include 'bookmarklet_include' %>" >URLを持ち出す！</a>リンクをブックマックバーにドラッグして登録しましょう！</p>
		<p>後は持ち出したいページで「URLを持ち出す！」をクリックするだけでOK!</p>
      </div>
    </div>
  </div>
  <div class="accordion-group">
    <div class="accordion-heading">
      <a class="accordion-toggle" data-toggle="collapse" data-parent="#add_accordion" href="#adac_collapseTwo">
        スマホで読みかけのページを持ち出すには？
      </a>
    </div>
    <div id="adac_collapseTwo" class="accordion-body collapse">
      <div class="accordion-inner">
        <p>詳しくは<a href="<%= url_for('/sp_bmlt') . '#' . include 'bookmarklet_include' %>" >スマホから持ち出す</a>ページで！</p>
      </div>
    </div>
  </div>
</div>


<ul class="nav nav-tabs" id="bm-tab">
<li class="<%= (1 - stash 'disp_channel') && 'active' %>" id="bmtab1"><a href="#tab_notvisited" data-toggle="bmlist_tab">未訪問</a></li>
<li class="<%= (stash 'disp_channel') && 'active' %>"><a href="#tab_visited" data-toggle="bmlist_tab">訪問済</a></li>
</ul>
<div class="tab-content">
<div class="tab-pane <%= (1 - stash 'disp_channel') && 'active' %>" id="tab_notvisited">
<%= include 'partial_bmlist', bookmark_list => (stash 'bookmarks_nonvisited') , list_exceeds=> (stash 'exceeds_nonvisited'), disp_channel=>0 %>
</div>
<div class="tab-pane <%= (stash 'disp_channel') && 'active' %>" id="tab_visited">
<%= include 'partial_bmlist', bookmark_list => (stash 'bookmarks_visited') , list_exceeds=> (stash 'exceeds_visited' ), disp_channel=>1 %>
</div>
</div>

<% if( (stash 'exceeds_visited') || (stash 'exceeds_nonvisited') ) { %>
<div class="accordion" id="old_accordion">
  <div class="accordion-group">
    <div class="accordion-heading">
      <a class="accordion-toggle" data-toggle="collapse" data-parent="#old_accordion" href="#olac_collapseOne">
        これより前に登録したリンクは？
      </a>
    </div>
    <div id="olac_collapseOne" class="accordion-body collapse">
      <div class="accordion-inner">
        <p>これより前に登録したページは表示できません。</p>
		<p>読み終わったページの登録を"削除"して整理すれば表示されます。</p>
      </div>
    </div>
  </div>
</div>
<% } %>

@@ signup.html.ep
% layout 'default';
% title 'Signup';
<h2>signup</h2>
<%= include 'partial_signup_form', formId => 'signup' %>

@@ welcome.html.ep
% layout 'default';
% title 'Welcome!';
<h4>URLToGo へようこそ！</h4>
<p><%= stash 'message' %></p>
<h4>どんなサービス？</h4>
<p>読みかけのページのアドレスをURLToGoに登録。別のPCやスマホからアクセスして続きが読めます。</p>
<h3>どうやって使うの？</h3>
<h4>URLを登録する</h4>
<p><a href="<%= url_for('/') %>">トップページ</a>にある
<h4>PCから</h4>
<ol>
<li>下の「このページをURLToGoに登録」リンクをブックマークバーにドラッグします。<br />
<a href="<%= include 'bookmarklet_include' %>" >このページをURLToGoに登録</a></li>
<li>ネットサーフィン中、持ち出したいページを開いているときに「このページをURLToGoに登録」をクリックします</li>
<li>「持ち出し成功！」のメッセージが出れば登録完了です！</li>
</ol>

@@ add_js.js.ep
%# 成功時はメッセージを返すだけ
alert("<%= stash 'message' %>");

@@ open_login.js.ep
%# 認証に失敗して登録できなかった場合は、window.openして登録画面に持って行く
open("http://www.google.com/", "null", "width=600,height=400,menubar=no,toolbar=no");


@@ bookmarklet_include.html.ep
%# bookmarkletのjsの中身
javascript:(function(){\
ul=encodeURIComponent(location.href);\
ti=encodeURIComponent(document.title);\
ep=(new%20Date).getTime();\
sr='<%= $self->req->url->to_abs->base . url_for('add') %>?epoch='+ep+'&url='+ul+'&title='+ti;\
window.open(sr,'_blank', 'width=600,height=400,menubar=no,toolbar=no');\
})();


@@ add.html.ep
% layout 'default';
%title '登録しました';
<h4><%= stash('message') %></h4>
<dl>
<dt><a href="<%= stash('bookmark_url') %>" target="_blank"><%= stash('bookmark_title') %></a></dt>
<dd><small><%= stash('bookmark_host') %></small></dd>
<dd><%= stash('bookmark_comment') %></dd>
</dl>
<div class="text-center"><a href="#" onClick="javascript:window.open('','_self');window.close();">Close</a></div>

@@ sp_bmlt.html.ep
% layout 'default';
% title 'URLを持ち出す';
<h4>スマホからURLを持ち出そう！</h4>

<ul class="nav nav-tabs" id="bm-tab">
<li class="active" id="bmtab1"><a href="#tab_prepare" data-toggle="bmlist_tab">準備する</a></li>
<li class=""><a href="#tab_use" data-toggle="bmlist_tab">使う</a></li>
</ul>
<div class="tab-content">
<div class="tab-pane active" id="tab_prepare">
<p>スマートフォンからURLを持ち出す準備は3ステップ。</p>
<h4>1.URLToGoに登録する</h4>
<p>このページを表示できているなら登録できてますね！:)</p>
<h4>2.「ブックマークに追加」する</h4>
<p>ブックマークの名前はお好みで変更してくださいね！</p>
<h4>3.アドレスを書き換える</h4>
<p>ブックマークを開いて、さっき登録したブックマークを「編集」します。</p>
<p>アドレスの欄の#より左側を削除してください！</p>
<dl class="dl-horizontal">
<dt>Before</dt>
<dd><em><%= url_for()->to_abs %>#</em>javascript:(function(){...</dd>
<dt>After</dt>
<dd>javascript:(function(){...</dd>
</dl>
<h4>4.準備OK!</h4>
<p>これで準備完了！</p>
</div>
<div class="tab-pane " id="tab_use">
<p>準備が出来たら、あとは簡単にURLを持ち出すことができます。</p>
<h4>持ち出したいページを見つけたら</h4>
<p>「準備」でブックマークに登録した、「URLToGo - URLを持ち出す」をクリックします。</p>
<p>「持ち出し成功！」のメッセージが出れば登録完了です。</p>
</div>
</div>

@@ error_happens.html.ep
% layout 'default';
% title 'ERROR happens!';
<h2>処理エラーが発生しました</h2>
<p>申し訳ありません。処理中にエラーが発生しました。</p>
<p><%= stash 'message' %></p>

