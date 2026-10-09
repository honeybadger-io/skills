#!/bin/bash
# Fixture apps for the honeybadger-get-started cases. Source this file, then call one of:
#   make_rails_app [--installed | --readme-only]   Rails app "Shop"
#   make_ember_app [--cdn]                          Ember app "storefront"
#
# --installed    honeybadger gem + config/honeybadger.yml
# --readme-only  README mentions Honeybadger, but the app does not use it
# --cdn          index.html loads honeybadger.js from the CDN and configures it

init_repo() {
  set -e
  git init -q -b main
  git config user.name "Shop Dev"
  git config user.email "dev@shop.example"
  git config commit.gpgsign false
}

commit_all() {
  git add -A
  GIT_AUTHOR_DATE="2026-09-01T10:00:00Z" GIT_COMMITTER_DATE="2026-09-01T10:00:00Z" git commit -q -m "$1"
}

make_rails_app() {
  init_repo
  mkdir -p app/controllers app/models config/environments config/initializers test bin
  cat > Gemfile <<'EOF'
source "https://rubygems.org"
ruby "3.4.2"
gem "rails", "~> 8.0"
gem "pg", "~> 1.5"
gem "puma", ">= 6.0"
EOF
  if [ "${1:-}" = "--installed" ]; then
    echo 'gem "honeybadger", "~> 6.0"' >> Gemfile
    cat > config/honeybadger.yml <<'EOF'
---
api_key: "<%= ENV['HONEYBADGER_API_KEY'] %>"
EOF
  fi
  cat > config/application.rb <<'EOF'
require_relative "boot"
require "rails/all"

module Shop
  class Application < Rails::Application
    config.load_defaults 8.0
  end
end
EOF
  cat > config/environments/production.rb <<'EOF'
Rails.application.configure do
  config.eager_load = true
  config.log_level = :info
end
EOF
  cat > app/controllers/application_controller.rb <<'EOF'
class ApplicationController < ActionController::Base
end
EOF
  cat > app/controllers/orders_controller.rb <<'EOF'
class OrdersController < ApplicationController
  def show
    @order = Order.find(params[:id])
  end
end
EOF
  cat > app/models/order.rb <<'EOF'
class Order < ApplicationRecord
end
EOF
  cat > Procfile <<'EOF'
web: bundle exec puma -C config/puma.rb
EOF
  if [ "${1:-}" = "--readme-only" ]; then
    cat > README.md <<'EOF'
# Shop

TODO: add error tracking. We used Honeybadger on the old storefront and liked it.
EOF
  else
    echo "# Shop" > README.md
  fi
  commit_all "Shop app"
}

make_ember_app() {
  init_repo
  mkdir -p app/routes app/templates tests
  cat > package.json <<'EOF'
{
  "name": "storefront",
  "version": "1.0.0",
  "private": true,
  "scripts": { "start": "ember serve", "build": "ember build --environment=production", "test": "ember test" },
  "devDependencies": {
    "ember-cli": "~6.2.0",
    "ember-source": "~6.2.0",
    "ember-data": "~5.3.0"
  }
}
EOF
  if [ "${1:-}" = "--cdn" ]; then
    cat > app/index.html <<'EOF'
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Storefront</title>
    <script src="//js.honeybadger.io/v6.10/honeybadger.min.js" type="text/javascript"></script>
    <script type="text/javascript">
      Honeybadger.configure({ apiKey: "hbp_fixture_key", environment: "production" });
    </script>
    {{content-for "head"}}
  </head>
  <body>
    {{content-for "body"}}
    <script src="{{rootURL}}assets/vendor.js"></script>
    <script src="{{rootURL}}assets/storefront.js"></script>
  </body>
</html>
EOF
  else
    cat > app/index.html <<'EOF'
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Storefront</title>
    {{content-for "head"}}
  </head>
  <body>
    {{content-for "body"}}
    <script src="{{rootURL}}assets/vendor.js"></script>
    <script src="{{rootURL}}assets/storefront.js"></script>
  </body>
</html>
EOF
  fi
  cat > app/app.js <<'EOF'
import Application from '@ember/application';
import Resolver from 'ember-resolver';
import config from 'storefront/config/environment';

export default class App extends Application {
  modulePrefix = config.modulePrefix;
  Resolver = Resolver;
}
EOF
  cat > app/router.js <<'EOF'
import EmberRouter from '@ember/routing/router';
import config from 'storefront/config/environment';

export default class Router extends EmberRouter {
  location = config.locationType;
  rootURL = config.rootURL;
}

Router.map(function () {
  this.route('products');
});
EOF
  cat > app/routes/products.js <<'EOF'
import Route from '@ember/routing/route';

export default class ProductsRoute extends Route {
  model() {
    return fetch('/api/products').then((r) => r.json());
  }
}
EOF
  echo "# Storefront" > README.md
  commit_all "Storefront app"
}
