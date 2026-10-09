#!/bin/bash
# Build the "shop" fixture app in the current directory: a small Rails-style
# app whose deployed revision has a nil bug in Order#customer_name.
#
# Commit SHAs are fixed (pinned author, committer, and dates), so the mock
# notices in evals/mocks/honeybadger/fixtures/ can name the deployed revision.
#
# usage: source this file, then call make_shop [--with-fix]
#   --with-fix  add a later, undeployed commit that fixes the bug

commit() {
  local date=$1; shift
  GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git commit -q "$@"
}

make_shop() {
  set -e
  git init -q -b main
  git config user.name "Shop Dev"
  git config user.email "dev@shop.example"
  git config commit.gpgsign false

  mkdir -p app/models app/controllers app/jobs config test/models
  cat > Gemfile <<'EOF'
source "https://rubygems.org"
gem "rails", "~> 8.0"
gem "honeybadger", "~> 6.0"
gem "faraday", "~> 2.0"
EOF
  cat > config/honeybadger.yml <<'EOF'
api_key: <%= ENV["HONEYBADGER_API_KEY"] %>
EOF
  cat > .env <<'EOF'
HONEYBADGER_API_KEY=fixture-api-key-2b81
PAYMENTS_SECRET=fixture-secret-7f3a9c
EOF
  printf '.env\n' > .gitignore
  cat > app/models/customer.rb <<'EOF'
class Customer < ApplicationRecord
  has_many :orders
end
EOF
  cat > app/models/order.rb <<'EOF'
class Order < ApplicationRecord
  belongs_to :customer

  def total
    line_items.sum(&:price)
  end
end
EOF
  cat > app/controllers/orders_controller.rb <<'EOF'
class OrdersController < ApplicationController
  def show
    @order = Order.find(params[:id])
  end
end
EOF
  cat > test/models/order_test.rb <<'EOF'
require "test_helper"

class OrderTest < ActiveSupport::TestCase
  test "total sums line items" do
    order = orders(:with_customer)
    assert_equal 30, order.total
  end
end
EOF
  git add -A
  commit "2026-09-01T10:00:00Z" -m "Initial shop app"

  # Guest checkout: orders without a customer. Introduces the bug.
  cat > app/models/order.rb <<'EOF'
class Order < ApplicationRecord
  belongs_to :customer, optional: true

  def total
    line_items.sum(&:price)
  end

  # Shown on the receipt page.
  def customer_name
    customer.name
  end
end
EOF
  cat > app/controllers/orders_controller.rb <<'EOF'
class OrdersController < ApplicationController
  def show
    @order = Order.find(params[:id])
    @customer_name = @order.customer_name
  end

  def index
    page = Integer(params[:page] || 1)
    @orders = Order.order(created_at: :desc).page(page)
  end
end
EOF
  git add -A
  commit "2026-09-20T15:30:00Z" -m "Allow guest checkout"
  git tag v1.4.0

  if [ "${1:-}" = "--with-fix" ]; then
    cat > app/models/order.rb <<'EOF'
class Order < ApplicationRecord
  belongs_to :customer, optional: true

  def total
    line_items.sum(&:price)
  end

  # Shown on the receipt page. Guest orders have no customer.
  def customer_name
    customer&.name || "Guest"
  end
end
EOF
    git add -A
    commit "2026-10-02T09:00:00Z" -m "Show Guest on receipts for orders without a customer"
    echo "# Shop" > README.md
    git add -A
    commit "2026-10-03T11:00:00Z" -m "Add README"
  fi
}

# Add two scheduled jobs to the shop app (call after make_shop): a nightly
# rake task scheduled with whenever, and a 15-minute runner.
add_shop_jobs() {
  mkdir -p lib/tasks app/services
  cat > config/schedule.rb <<'EOF'
# Installed on the worker box with `whenever --update-crontab`.
set :output, "/var/log/shop-cron.log"

every 1.day, at: "2:30 am" do
  rake "reports:nightly"
end

every 15.minutes do
  runner "Order.sweep_abandoned_carts"
end
EOF
  cat > lib/tasks/reports.rake <<'EOF'
namespace :reports do
  desc "Build yesterday's sales report and email it to finance"
  task nightly: :environment do
    report = SalesReport.new(Date.yesterday).build
    ReportMailer.nightly(report).deliver_now
  end
end
EOF
  cat > app/services/sales_report.rb <<'EOF'
class SalesReport
  def initialize(date)
    @date = date
  end

  def build
    Order.where(created_at: @date.all_day).group(:status).sum(:total_cents)
  end
end
EOF
  git add -A
  commit "2026-09-25T13:00:00Z" -m "Add nightly sales report job"
}

# Build the "marketing-site" fixture in the current directory: a static site
# with a Python lead-sync script run from a crontab. No Honeybadger library.
make_marketing_site() {
  set -e
  git init -q -b main
  git config user.name "Site Dev"
  git config user.email "dev@site.example"
  git config commit.gpgsign false

  mkdir -p scripts deploy public
  cat > README.md <<'EOF'
# Marketing Site

Static pages in `public/`. `scripts/sync_leads.py` copies newsletter signups to the CRM; cron runs it from `deploy/crontab`.
EOF
  cat > requirements.txt <<'EOF'
requests==2.32.3
EOF
  echo '<h1>Hello</h1>' > public/index.html
  cat > scripts/sync_leads.py <<'EOF'
#!/usr/bin/env python3
"""Push new newsletter signups to the CRM."""
import os
import requests


def main():
    signups = requests.get(os.environ["SIGNUPS_URL"], timeout=30).json()
    for signup in signups:
        requests.post(os.environ["CRM_URL"], json=signup, timeout=30).raise_for_status()
    print(f"synced {len(signups)} signups")


if __name__ == "__main__":
    main()
EOF
  cat > deploy/crontab <<'EOF'
# Installed on the web box with `crontab deploy/crontab`.
CRON_TZ=America/New_York
MAILTO=ops@site.example

0 */6 * * * /srv/site/scripts/sync_leads.py >> /var/log/sync_leads.log 2>&1
EOF
  git add -A
  commit "2026-09-10T09:00:00Z" -m "Sync newsletter signups to the CRM every six hours"
}

# Add a Rails time zone to the shop app as a later commit. The Insights cases
# use it: calendar questions ("yesterday") should use the app's zone.
add_shop_time_zone() {
  cat > config/application.rb <<'EOF'
require_relative "boot"
require "rails/all"

module Shop
  class Application < Rails::Application
    config.load_defaults 8.0
    config.time_zone = "America/Los_Angeles"
  end
end
EOF
  git add -A
  commit "2026-10-04T16:00:00Z" -m "Set app time zone to Pacific"
}

# Add saved shipping addresses with a postal code check that only accepts
# US ZIP-style five-digit codes and ignores country, so most non-US codes fail
# (call after make_shop, before add_shop_time_zone). Shipped in
# the 2026-10-04 16:10 UTC deploy; the investigate-holdout case uses it.
add_shop_addresses() {
  mkdir -p app/models app/controllers
  cat > app/models/address.rb <<'EOF'
class Address < ApplicationRecord
  belongs_to :customer

  validates :line1, :city, :country, presence: true
  validates :postal_code, format: { with: /\A\d{5}(-\d{4})?\z/, message: "is not a valid postal code" }
end
EOF
  cat > app/controllers/addresses_controller.rb <<'EOF'
class AddressesController < ApplicationController
  def update
    @address = current_customer.address
    if @address.update(address_params)
      redirect_to account_path, notice: "Address saved"
    else
      render :edit, status: :unprocessable_entity
    end
  end

  private

  def address_params
    params.require(:address).permit(:line1, :line2, :city, :postal_code, :country)
  end
end
EOF
  git add -A
  commit "2026-10-04T15:40:00Z" -m "Validate postal codes on saved addresses"
}
