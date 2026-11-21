// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';

import 'account.dart';
import 'orders_screen.dart';
import 'stock_screens.dart';

/// Today: hello, the numbers that matter (orders to receive, items out of stock, deliveries today), stock by place
/// as bars, and quick buttons for the jobs you are allowed to do.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with LoadsData {
  @override
  Future<dynamic> load(Api api) async {
    final s = AppScope.of(context).session;
    await loadAccount(api, s);                             // permissions and locations may have changed
    s.changed();
    Future<dynamic> maybe(bool allowed, String path) => allowed ? api.get(path).catchError((_) => null) : Future.value(null);
    final r = await Future.wait([
      maybe(s.can('orders'), '/orders'),
      maybe(s.can('view_stock'), '/stock'),
      maybe(s.can('delivery') || s.can('view_stock'), '/stock/deliveries'),
    ]);
    return {'orders': r[0], 'stock': r[1], 'deliveries': r[2]};
  }

  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context).session;
    return AsyncView<dynamic>(
      future: data,
      onRetry: reload,
      builder: (context, d) {
        final orders = (((d['orders'] ?? const {}) as Map)['orders'] ?? const []) as List;
        final levels = ((((d['stock'] ?? const {}) as Map)['levels'] ?? const []) as List).cast<Map>();
        final trips = ((((d['deliveries'] ?? const {}) as Map)['deliveries'] ?? const []) as List).cast<Map>();
        final toReceive = orders.where((o) => (o as Map)['state'] == 'saved').length;
        final out = levels.where((l) => Fmt.number(l['qty']) <= 0).length;
        final today = trips.where((t) => Fmt.daysFromToday(t['date']) == 0).length;
        final byPlace = <String, int>{};
        for (final l in levels) {
          if (Fmt.number(l['qty']) > 0) byPlace['${l['location_name']}'] = (byPlace['${l['location_name']}'] ?? 0) + 1;
        }
        return LargeTitlePage(
          title: 'Hello${s.name.isEmpty ? '' : ', ${s.name.split(' ').first}'}',
          subtitle: businessName(s),
          onRefresh: reload,
          children: [
            StatGrid(tiles: [
              if (s.can('orders')) StatTile(label: 'Orders to receive', value: toReceive, icon: Icons.receipt_long_rounded, color: SystemColors.orange, onTap: () => push(context, const Scaffold(body: OrdersScreen()))),
              if (s.can('view_stock')) StatTile(label: 'Items out of stock', value: out, icon: Icons.warning_amber_rounded, color: out > 0 ? SystemColors.red : SystemColors.green, onTap: () => push(context, const Scaffold(body: StockScreen()))),
              if (s.can('delivery') || s.can('view_stock')) StatTile(label: 'Deliveries today', value: today, icon: Icons.local_shipping_rounded, color: SystemColors.indigo, onTap: () => push(context, const Scaffold(body: DeliveriesScreen()))),
              if (s.can('view_stock')) StatTile(label: 'Items in stock', value: levels.length - out, icon: Icons.inventory_2_rounded, color: SystemColors.teal),
            ]),
            if (byPlace.isNotEmpty) ...[
              const SectionHeader('Items in stock by place'),
              SoftCard(child: BarChart(values: byPlace.values.toList(), labels: byPlace.keys.map((k) => k.length > 8 ? k.substring(0, 8) : k).toList(), height: 170)),
            ],
            const SectionHeader('Your jobs'),
            GroupedList(children: [
              if (s.can('kitchen')) const RowItem(title: 'Kitchen', subtitle: "This week's target, production, ingredients", icon: Icons.soup_kitchen_rounded, iconColor: SystemColors.orange),
              if (s.can('closing')) const RowItem(title: 'Closing', subtitle: 'Count stock, enter sales, note issues', icon: Icons.fact_check_rounded, iconColor: SystemColors.green),
              if (s.can('warehouse_out')) const RowItem(title: 'Send', subtitle: 'Warehouse out to each location', icon: Icons.local_shipping_rounded, iconColor: SystemColors.indigo),
              if (s.can('orders')) const RowItem(title: 'Orders', subtitle: 'Send to suppliers, receive deliveries', icon: Icons.receipt_long_rounded, iconColor: SystemColors.teal),
              const RowItem(title: 'Everything else', subtitle: 'AI chat, recipes, costing, bills, team - under More', icon: Icons.apps_rounded, iconColor: SystemColors.gray),
            ]),
          ],
        );
      },
    );
  }
}
