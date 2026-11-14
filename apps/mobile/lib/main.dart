// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

// Kitchen Stock & Costing - phone app. The server is chosen at build time: --dart-define=API_BASE=https://...
// Same /api/v1 as the web app; each screen shows only to users whose role allows it (the server checks again).
import 'package:flutter/material.dart';

import 'core/api.dart';
import 'core/session.dart';
import 'screens/closing_screen.dart';
import 'screens/deliveries_screen.dart';
import 'screens/home_screen.dart';
import 'screens/kitchen_screen.dart';
import 'screens/login_screen.dart';
import 'screens/orders_screen.dart';
import 'screens/stock_screen.dart';
import 'screens/warehouse_out_screen.dart';

const apiBase = String.fromEnvironment('API_BASE', defaultValue: 'http://10.0.2.2:8861');

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final session = await Session.load();
  runApp(KitchenApp(api: Api(apiBase, session), session: session));
}

class KitchenApp extends StatelessWidget {
  const KitchenApp({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  Widget build(BuildContext context) {
    const seed = Color(0xFF0F766E);
    return MaterialApp(
      title: 'Kitchen',
      theme: ThemeData(colorSchemeSeed: seed, useMaterial3: true),
      darkTheme: ThemeData(colorSchemeSeed: seed, brightness: Brightness.dark, useMaterial3: true),
      home: ListenableBuilder(
        listenable: session,
        builder: (context, _) => session.signedIn ? Shell(api: api, session: session) : LoginScreen(api: api, session: session),
      ),
    );
  }
}

/// One tab per daily task the user's role allows.
class Shell extends StatefulWidget {
  const Shell({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  State<Shell> createState() => _ShellState();
}

class TabSpec {
  const TabSpec(this.label, this.icon, this.perm, this.module, this.build);
  final String label;
  final IconData icon;
  final String perm;
  final String module;
  final Widget Function() build;
}

class _ShellState extends State<Shell> {
  int index = 0;

  @override
  Widget build(BuildContext context) {
    final s = widget.session;
    final api = widget.api;
    final all = <TabSpec>[
      TabSpec('Today', Icons.home_outlined, '', '', () => HomeScreen(api: api, session: s)),
      TabSpec('Kitchen', Icons.soup_kitchen_outlined, 'kitchen', 'kitchen', () => KitchenScreen(api: api, session: s)),
      TabSpec('Closing', Icons.fact_check_outlined, 'closing', 'closing', () => ClosingScreen(api: api, session: s)),
      TabSpec('Send', Icons.local_shipping_outlined, 'warehouse_out', 'inventory', () => WarehouseOutScreen(api: api, session: s)),
      TabSpec('Orders', Icons.receipt_long_outlined, 'orders', 'orders', () => OrdersScreen(api: api, session: s)),
      TabSpec('Deliveries', Icons.delivery_dining_outlined, 'delivery', 'inventory', () => DeliveriesScreen(api: api)),
      TabSpec('Stock', Icons.inventory_2_outlined, 'view_stock', 'inventory', () => StockScreen(api: api)),
    ];
    final tabs = all.where((t) => (t.perm.isEmpty || s.can(t.perm)) && (t.module.isEmpty || s.moduleOn(t.module))).toList();
    if (index >= tabs.length) index = 0;
    return Scaffold(
      appBar: AppBar(
        title: Text(s.businessName.isEmpty ? 'Kitchen' : s.businessName),
        actions: [IconButton(icon: const Icon(Icons.logout), tooltip: 'Log out', onPressed: s.clear)],
      ),
      body: tabs[index].build(),
      bottomNavigationBar: tabs.length < 2
          ? null
          : NavigationBar(
              selectedIndex: index,
              onDestinationSelected: (i) => setState(() => index = i),
              destinations: [for (final t in tabs) NavigationDestination(icon: Icon(t.icon), label: t.label)],
            ),
    );
  }
}
