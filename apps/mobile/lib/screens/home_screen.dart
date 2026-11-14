// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/session.dart';
import '../core/ui.dart';

/// Today: the business, the user's tasks as tabs below; refreshes roles and locations from the server.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late Future<Map<String, dynamic>> me = load();

  Future<Map<String, dynamic>> load() async {
    final me = await widget.api.get('/me') as Map<String, dynamic>;
    final noBusiness = me['tenant'] == null || me['tenant'] == '';
    final business = noBusiness ? <String, dynamic>{} : await widget.api.get('/me/business') as Map<String, dynamic>;
    await widget.session.refresh(me, business);
    return me;
  }

  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: () async => setState(() => me = load()),
        child: Loader<Map<String, dynamic>>(
          future: me,
          builder: (context, m) {
            final s = widget.session;
            final tasks = <String>[
              if (s.can('kitchen')) 'Kitchen: see this week\'s target, record production and ingredients',
              if (s.can('closing')) 'Closing: count stock, note issues, enter sales',
              if (s.can('warehouse_out')) 'Send: warehouse out to each location',
              if (s.can('orders')) 'Orders: reorder recommendation, purchase orders, receive',
              if (s.can('delivery')) 'Deliveries: what leaves the warehouse',
              if (s.can('view_costs')) 'Costs and setup: open the web app on your phone or computer',
            ];
            return ListView(padding: const EdgeInsets.all(16), children: [
              Text('Hello ${m['name'] ?? ''}', style: Theme.of(context).textTheme.headlineSmall),
              Text(s.businessName),
              const SizedBox(height: 16),
              for (final t in tasks) Card(child: ListTile(title: Text(t))),
              if (tasks.isEmpty) const Card(child: ListTile(title: Text('No tasks yet - ask your owner to give you a role.'))),
            ]);
          },
        ),
      );
}
