// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:grepx_app/grepx_app.dart';
import 'package:url_launcher/url_launcher.dart';

import 'account.dart';

/// Purchase orders: "to receive" first; open one to send it on WhatsApp, copy it, or receive it into stock.
class OrdersScreen extends StatefulWidget {
  const OrdersScreen({super.key});

  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> with LoadsData {
  String show = 'open';

  @override
  Future<dynamic> load(Api api) => api.get('/orders');

  @override
  Widget build(BuildContext context) => AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, d) {
          final all = (((d as Map)['orders'] ?? const []) as List).cast<Map>();
          final open = all.where((o) => o['state'] == 'saved').toList();
          final shown = show == 'open' ? open : all;
          return LargeTitlePage(
            title: 'Orders',
            onRefresh: reload,
            children: [
              Segments<String>(value: show, options: {'open': 'To receive ${open.length}', 'all': 'All ${all.length}'}, onChanged: (v) => setState(() => show = v)),
              const SizedBox(height: Gap.l),
              if (shown.isEmpty) const EmptyState(icon: Icons.receipt_long_outlined, title: 'No orders here', text: 'Orders come from the reorder recommendation in the web app.'),
              for (final o in shown)
                Padding(
                  padding: const EdgeInsets.only(bottom: Gap.s),
                  child: SoftCard(
                    onTap: () async {
                      await push(context, OrderScreen(order: o));
                      reload();
                    },
                    child: Row(children: [
                      const IconTile(Icons.receipt_long_rounded, color: SystemColors.teal, size: 40),
                      const SizedBox(width: Gap.m),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text('${o['supplier_name']}', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                          Text('${o['number']} · ${((o['lines'] ?? const []) as List).length} lines', style: TextStyle(color: context.secondaryText, fontSize: 13)),
                        ]),
                      ),
                      StatusPill(o['state'] == 'saved' ? 'to receive' : '${o['state']}', color: o['state'] == 'saved' ? SystemColors.orange : null),
                    ]),
                  ),
                ),
            ],
          );
        },
      );
}

class OrderScreen extends StatefulWidget {
  const OrderScreen({super.key, required this.order});
  final Map order;

  @override
  State<OrderScreen> createState() => _OrderScreenState();
}

class _OrderScreenState extends State<OrderScreen> {
  final arrived = <String, TextEditingController>{};

  Future<void> _receive() async {
    final o = widget.order;
    final api = AppScope.of(context).api;
    final ok = await attempt(context, () => api.post('/orders/${o['id']}/receive', {'lines': readQty(arrived, keepZero: true)}), done: 'Received into stock');
    if (ok != null && mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final o = widget.order;
    final lines = ((o['lines'] ?? const []) as List).cast<Map>();
    final text = '${o['text'] ?? ''}';
    final phone = '${o['supplier_phone'] ?? ''}'.replaceAll(RegExp(r'\D'), '');
    return DetailPage(
      title: '${o['number']}',
      bottom: o['state'] == 'saved' ? FilledButton.icon(onPressed: _receive, icon: const Icon(Icons.move_to_inbox_rounded), label: const Text('Receive into stock')) : null,
      children: [
        Row(children: [
          if (phone.isNotEmpty)
            Expanded(
              child: FilledButton.icon(
                style: FilledButton.styleFrom(backgroundColor: const Color(0xFF25D366)),
                onPressed: () => launchUrl(Uri.parse('https://wa.me/$phone?text=${Uri.encodeComponent(text)}'), mode: LaunchMode.externalApplication),
                icon: const Icon(Icons.chat_rounded),
                label: const Text('WhatsApp'),
              ),
            ),
          if (phone.isNotEmpty) const SizedBox(width: Gap.m),
          Expanded(
            child: OutlinedButton.icon(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: text));
                showBanner('Order copied', kind: BannerKind.success);
              },
              icon: const Icon(Icons.copy_rounded),
              label: const Text('Copy'),
            ),
          ),
        ]),
        const SectionHeader('The order'),
        SoftCard(child: SelectableText(text, style: const TextStyle(height: 1.4))),
        if (o['state'] == 'saved') ...[
          const SectionHeader('What arrived'),
          Text('Change a quantity if the delivery differs.', style: TextStyle(color: context.secondaryText)),
          const SizedBox(height: Gap.s),
          QtyList(rows: [for (final l in lines) {'item_id': l['item_id'], 'name': l['item_name'], 'unit': l['unit'], 'qty': l['qty']}], controllers: arrived),
        ],
      ],
    );
  }
}
