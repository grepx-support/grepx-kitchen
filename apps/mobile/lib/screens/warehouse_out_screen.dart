// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/session.dart';
import '../core/ui.dart';

/// INV-02/03: the suggestion for a location; accept it, change or clear lines, send.
class WarehouseOutScreen extends StatefulWidget {
  const WarehouseOutScreen({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  State<WarehouseOutScreen> createState() => _WarehouseOutScreenState();
}

class _WarehouseOutScreenState extends State<WarehouseOutScreen> {
  late String to = pickLocation(widget.session, (l) => l['holding'] != true);
  late Future<Map<String, dynamic>> plan = load();
  final qty = <String, TextEditingController>{};

  Future<Map<String, dynamic>> load() async => await widget.api.get('/stock/warehouse-out?to_location_id=$to') as Map<String, dynamic>;

  @override
  Widget build(BuildContext context) {
    if (to.isEmpty) return const Center(child: Text('Set up a location to send to first.'));
    return Loader<Map<String, dynamic>>(
      future: plan,
      builder: (context, p) {
        final lines = [for (final l in p['lines'] as List) Map<String, dynamic>.from(l as Map)];
        return ListView(padding: const EdgeInsets.all(16), children: [
          LocationPicker(session: widget.session, value: to, where: (l) => l['holding'] != true, onChanged: (v) => setState(() {
                to = v;
                qty.clear();
                plan = load();
              })),
          const SizedBox(height: 8),
          Text('Enough for ${p['days_of_cover']} days. Change or clear any line.'),
          if (lines.isEmpty) const Padding(padding: EdgeInsets.all(16), child: Text('Nothing suggested (no usage history yet, or enough stock there).')),
          QtyList(
              rows: [for (final l in lines) {'item_id': l['item_id'], 'name': l['name'], 'unit': l['unit'], 'qty': l['suggested'], 'hint': 'there ${fmt(l['at_location'])} · warehouse ${fmt(l['at_holding'])}'}],
              controllers: qty,
              label: 'Send'),
          const SizedBox(height: 12),
          FilledButton(
            onPressed: lines.isEmpty
                ? null
                : () async {
                    final ls = readQty(qty);
                    if (ls.isEmpty) return;
                    final ok = await attempt(context,
                        () => widget.api.post('/stock/send', {'from_location_id': p['from_location_id'], 'to_location_id': to, 'lines': ls}), done: 'Sent');
                    if (ok != null) setState(() {
                      qty.clear();
                      plan = load();
                    });
                  },
            child: const Text('Send stock'),
          ),
        ]);
      },
    );
  }
}
