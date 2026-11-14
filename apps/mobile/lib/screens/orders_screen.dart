// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/api.dart';
import '../core/session.dart';
import '../core/ui.dart';

/// ORD-02..08: open purchase orders - share on WhatsApp, receive (with changed quantities). New orders: web app.
class OrdersScreen extends StatefulWidget {
  const OrdersScreen({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> {
  late Future<dynamic> orders = widget.api.get('/orders');

  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: () async => setState(() => orders = widget.api.get('/orders')),
        child: Loader<dynamic>(
          future: orders,
          builder: (context, data) {
            final list = [for (final o in (data as Map)['orders'] as List) Map<String, dynamic>.from(o as Map)];
            return ListView(padding: const EdgeInsets.all(16), children: [
              const Text('Create orders from the recommendation in the web app; open one here to send or receive it.'),
              for (final o in list)
                Card(
                  child: ListTile(
                    title: Text('${o['number']} · ${o['supplier_name']}'),
                    subtitle: Text('${o['state']} · ${(o['lines'] as List).length} lines'),
                    onTap: () async {
                      await Navigator.push(context, MaterialPageRoute(builder: (_) => OrderScreen(api: widget.api, order: o)));
                      setState(() => orders = widget.api.get('/orders'));
                    },
                  ),
                ),
            ]);
          },
        ),
      );
}

class OrderScreen extends StatefulWidget {
  const OrderScreen({super.key, required this.api, required this.order});
  final Api api;
  final Map<String, dynamic> order;

  @override
  State<OrderScreen> createState() => _OrderScreenState();
}

class _OrderScreenState extends State<OrderScreen> {
  final qty = <String, TextEditingController>{};

  @override
  Widget build(BuildContext context) {
    final o = widget.order;
    final lines = [for (final l in o['lines'] as List) Map<String, dynamic>.from(l as Map)];
    final phone = (o['supplier_phone'] ?? '').toString().replaceAll(RegExp(r'\D'), '');
    return Scaffold(
      appBar: AppBar(title: Text(o['number'].toString())),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        SelectableText(o['text']?.toString() ?? ''),
        Wrap(spacing: 8, children: [
          OutlinedButton(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: o['text']?.toString() ?? ''));
              if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Copied')));
            },
            child: const Text('Copy text'),
          ),
          if (phone.isNotEmpty)
            OutlinedButton(
              onPressed: () => launchUrl(Uri.parse('https://wa.me/$phone?text=${Uri.encodeComponent(o['text']?.toString() ?? '')}'),
                  mode: LaunchMode.externalApplication),
              child: const Text('WhatsApp'),
            ),
        ]),
        if (o['state'] == 'saved') ...[
          const Divider(height: 32),
          Text('Receive', style: Theme.of(context).textTheme.titleLarge),
          const Text('Change a quantity if the delivery differs.'),
          QtyList(rows: [for (final l in lines) {'item_id': l['item_id'], 'name': l['item_name'], 'unit': l['unit'], 'qty': l['qty']}], controllers: qty, label: 'Arrived'),
          FilledButton(
            onPressed: () async {
              final ok = await attempt(context, () => widget.api.post('/orders/${o['id']}/receive', {'lines': readQty(qty, keepZero: true)}),
                  done: 'Received into stock');
              if (ok != null && context.mounted) Navigator.pop(context);
            },
            child: const Text('Receive into stock'),
          ),
        ],
      ]),
    );
  }
}
