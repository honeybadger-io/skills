#!/bin/bash
source "$(dirname "$0")/../_shared/make-shop.sh"
make_shop
# The backup an earlier update_dashboard left behind: the dashboard as it was before that update.
cp "$(dirname "$0")/../mocks/honeybadger/fixtures/dashboard-dQ7xRk.json" honeybadger-dashboard-dQ7xRk-20261008T115500.json
