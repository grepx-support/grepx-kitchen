// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';

import 'account.dart';
import 'closing_screen.dart';
import 'home_screen.dart';
import 'kitchen_screen.dart';
import 'orders_screen.dart';
import 'stock_screens.dart';

/// Kitchen Stock & Costing: Today, then the daily jobs this person may do (by permission and the business's
/// modules) - the first four fit the tab bar - and More: every other page of the web app, signed in.
final kitchenProduct = Product(
  key: 'kitchen',
  name: 'Kitchen',
  logo: '🍳',
  color: const Color(0xFF0F766E),
  tagline: 'Stock, costing and the daily jobs.',
  afterSignIn: loadAccount,
  notices: kitchenNotices,
  tabs: (api, s) {
    if (!s.signedIn) return const [];                      // staff only: the app opens on sign-in
    final jobs = <(String, String, AppTab)>[
      ('kitchen', 'kitchen', AppTab(label: 'Kitchen', icon: Icons.soup_kitchen_outlined, activeIcon: Icons.soup_kitchen_rounded, build: (_) => const KitchenScreen())),
      ('closing', 'closing', AppTab(label: 'Closing', icon: Icons.fact_check_outlined, activeIcon: Icons.fact_check_rounded, build: (_) => const ClosingScreen())),
      ('warehouse_out', 'inventory', AppTab(label: 'Send', icon: Icons.local_shipping_outlined, activeIcon: Icons.local_shipping_rounded, build: (_) => const SendScreen())),
      ('orders', 'orders', AppTab(label: 'Orders', icon: Icons.receipt_long_outlined, activeIcon: Icons.receipt_long_rounded, build: (_) => const OrdersScreen())),
      ('delivery', 'inventory', AppTab(label: 'Deliveries', icon: Icons.delivery_dining_outlined, activeIcon: Icons.delivery_dining_rounded, build: (_) => const DeliveriesScreen())),
      ('view_stock', 'inventory', AppTab(label: 'Stock', icon: Icons.inventory_2_outlined, activeIcon: Icons.inventory_2_rounded, build: (_) => const StockScreen())),
    ];
    final mine = [for (final (perm, module, tab) in jobs) if (s.can(perm) && moduleOn(s, module)) tab];
    return [
      AppTab(label: 'Today', icon: Icons.home_outlined, activeIcon: Icons.home_rounded, audience: Audience.signedIn, build: (_) => const HomeScreen()),
      ...mine.take(3),                                     // a phone bar holds five: Today, three jobs, More
      AppTab(label: 'More', icon: Icons.apps_rounded, audience: Audience.signedIn, build: (_) => const WebScreen(key: ValueKey('more'), path: '#/')),
    ];
  },
);

/// What the kitchen tells you about: an order waiting to be received, stock that ran out, stock sent today.
Future<List<Notice>> kitchenNotices(Api api, Session s) async {
  if (!s.signedIn) return const [];
  final out = <Notice>[];
  if (s.can('orders')) {
    for (final o in ((((await api.get('/orders')) as Map)['orders'] ?? const []) as List).cast<Map>().where((o) => o['state'] == 'saved')) {
      out.add(Notice(
        id: 'order:${o['id']}:saved',
        title: 'Order to receive',
        body: '${o['number']} from ${o['supplier_name']}',
        icon: Icons.receipt_long_rounded,
        color: SystemColors.orange,
        open: (c) => push(c, OrderScreen(order: o)),
      ));
    }
  }
  if (s.can('view_stock')) {
    final day = Fmt.today().toIso8601String().substring(0, 10);
    for (final l in ((((await api.get('/stock')) as Map)['levels'] ?? const []) as List).cast<Map>().where((l) => Fmt.number(l['qty']) <= 0)) {
      out.add(Notice(id: 'out:${l['item_name']}:${l['location_name']}:$day', title: '${l['item_name']} ran out', body: 'at ${l['location_name']}', icon: Icons.warning_amber_rounded, color: SystemColors.red));
    }
  }
  if (s.can('delivery') || s.can('view_stock')) {
    for (final t in ((((await api.get('/stock/deliveries')) as Map)['deliveries'] ?? const []) as List).cast<Map>().where((t) => Fmt.daysFromToday(t['date']) == 0)) {
      out.add(Notice(id: 'trip:${t['id'] ?? '${t['from']}-${t['to']}-${t['date']}'}', title: 'Stock on its way', body: '${t['from']} → ${t['to']}', icon: Icons.local_shipping_rounded, color: SystemColors.indigo));
    }
  }
  return out;
}
