// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';

import 'account.dart';

/// Stock on hand (search, by location), sending stock out of the warehouse, and the deliveries that left it.

class StockScreen extends StatefulWidget {
  const StockScreen({super.key});

  @override
  State<StockScreen> createState() => _StockScreenState();
}

class _StockScreenState extends State<StockScreen> with LoadsData {
  String query = '', where = '';

  @override
  Future<dynamic> load(Api api) => api.get('/stock');

  @override
  Widget build(BuildContext context) => AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, d) {
          final rows = (((d as Map)['levels'] ?? const []) as List).cast<Map>();
          final places = {for (final r in rows) '${r['location_name']}'}.toList()..sort();
          final shown = rows.where((r) => (where.isEmpty || r['location_name'] == where) && '${r['item_name']}'.toLowerCase().contains(query.toLowerCase())).toList();
          final byPlace = <String, List<Map>>{};
          for (final r in shown) {
            byPlace.putIfAbsent('${r['location_name']}', () => []).add(r);
          }
          return LargeTitlePage(
            title: 'Stock',
            onRefresh: reload,
            children: [
              TextField(onChanged: (v) => setState(() => query = v), decoration: const InputDecoration(hintText: 'Find an item', prefixIcon: Icon(Icons.search_rounded))),
              const SizedBox(height: Gap.m),
              SizedBox(
                height: 40,
                child: ListView(scrollDirection: Axis.horizontal, children: [
                  for (final p in ['', ...places])
                    Padding(
                      padding: const EdgeInsets.only(right: Gap.s),
                      child: ChoiceChip(label: Text(p.isEmpty ? 'Everywhere' : p), selected: where == p, onSelected: (_) => setState(() => where = p)),
                    ),
                ]),
              ),
              if (shown.isEmpty) const EmptyState(icon: Icons.inventory_2_outlined, title: 'Nothing found'),
              for (final e in byPlace.entries) ...[
                SectionHeader(e.key),
                GroupedList(children: [
                  for (final r in e.value)
                    RowItem(
                      title: '${r['item_name']}',
                      value: '${qty(r['qty'])} ${r['unit'] ?? ''}',
                      trailing: Fmt.number(r['qty']) <= 0 ? const Padding(padding: EdgeInsets.only(left: 8), child: StatusPill('out')) : null,
                    ),
                ]),
              ],
            ],
          );
        },
      );
}

class SendScreen extends StatefulWidget {
  const SendScreen({super.key});

  @override
  State<SendScreen> createState() => _SendScreenState();
}

class _SendScreenState extends State<SendScreen> with LoadsData {
  String to = '';
  final amounts = <String, TextEditingController>{};

  @override
  Future<dynamic> load(Api api) {
    if (to.isEmpty) to = pickLocation(AppScope.of(context).session, (l) => l['holding'] != true);
    return to.isEmpty ? Future.value(null) : api.get('/stock/warehouse-out?to_location_id=$to');
  }

  Future<void> _send(Map p) async {
    final lines = readQty(amounts);
    if (lines.isEmpty) {
      showBanner('Nothing to send yet');
      return;
    }
    final api = AppScope.of(context).api;
    final ok = await attempt(context, () => api.post('/stock/send', {'from_location_id': p['from_location_id'], 'to_location_id': to, 'lines': lines}), done: 'Sent - on its way');
    if (ok == null) return;
    amounts.clear();
    reload();
  }

  @override
  Widget build(BuildContext context) => AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, p) {
          if (p == null) return const LargeTitlePage(title: 'Send', children: [EmptyState(icon: Icons.local_shipping_outlined, title: 'Set up a location to send to first')]);
          final lines = ((p['lines'] ?? const []) as List).cast<Map>();
          return LargeTitlePage(
            title: 'Send',
            subtitle: 'Enough for ${p['days_of_cover']} days - change or clear any line',
            onRefresh: reload,
            children: [
              LocationPicker(value: to, where: (l) => l['holding'] != true, onChanged: (v) {
                to = v;
                amounts.clear();
                reload();
              }),
              const SizedBox(height: Gap.m),
              if (lines.isEmpty) const EmptyState(icon: Icons.check_circle_outline_rounded, title: 'Nothing to send', text: 'Enough stock there, or no usage history yet.'),
              if (lines.isNotEmpty) ...[
                QtyList(
                  rows: [for (final l in lines) {'item_id': l['item_id'], 'name': l['name'], 'unit': l['unit'], 'qty': l['suggested'], 'hint': 'there ${qty(l['at_location'])} · warehouse ${qty(l['at_holding'])}'}],
                  controllers: amounts,
                ),
                const SizedBox(height: Gap.l),
                FilledButton.icon(onPressed: () => _send(p as Map), icon: const Icon(Icons.local_shipping_rounded), label: const Text('Send stock')),
              ],
            ],
          );
        },
      );
}

class DeliveriesScreen extends StatefulWidget {
  const DeliveriesScreen({super.key});

  @override
  State<DeliveriesScreen> createState() => _DeliveriesScreenState();
}

class _DeliveriesScreenState extends State<DeliveriesScreen> with LoadsData {
  @override
  Future<dynamic> load(Api api) => api.get('/stock/deliveries');

  @override
  Widget build(BuildContext context) => AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, d) {
          final trips = (((d as Map)['deliveries'] ?? const []) as List).cast<Map>();
          return LargeTitlePage(
            title: 'Deliveries',
            onRefresh: reload,
            children: [
              if (trips.isEmpty) const EmptyState(icon: Icons.delivery_dining_outlined, title: 'Nothing has left the warehouse yet'),
              for (final t in trips)
                Padding(
                  padding: const EdgeInsets.only(bottom: Gap.m),
                  child: SoftCard(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        const IconTile(Icons.local_shipping_rounded, color: SystemColors.indigo, size: 36),
                        const SizedBox(width: Gap.m),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text('${t['from']}  →  ${t['to']}', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                            Text('${Fmt.day(t['date'])} · sent by ${t['by'] ?? ''}', style: TextStyle(color: context.secondaryText, fontSize: 13)),
                          ]),
                        ),
                      ]),
                      const SizedBox(height: Gap.m),
                      for (final l in ((t['lines'] ?? const []) as List).cast<Map>())
                        Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Row(children: [
                            Expanded(child: Text('${l['item_name']}')),
                            Text('${qty(l['qty'])} ${l['unit'] ?? ''}', style: const TextStyle(fontWeight: FontWeight.w600)),
                          ]),
                        ),
                    ]),
                  ),
                ),
            ],
          );
        },
      );
}
