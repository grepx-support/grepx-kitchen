// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/session.dart';
import '../core/ui.dart';

/// KIT-03..09: this week's target (finished goods, batches, ingredients to buy), record production and ingredients used.
class KitchenScreen extends StatefulWidget {
  const KitchenScreen({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  State<KitchenScreen> createState() => _KitchenScreenState();
}

class _KitchenScreenState extends State<KitchenScreen> {
  late String location = pickLocation(widget.session, (l) => l['kind'] == 'kitchen');
  late Future<Map<String, dynamic>> target = load();
  final made = <String, TextEditingController>{};
  final used = <String, TextEditingController>{};

  Future<Map<String, dynamic>> load() async => await widget.api.get('/kitchen/target?location_id=$location') as Map<String, dynamic>;

  void reload() => setState(() {
        made.clear();
        used.clear();
        target = load();
      });

  @override
  Widget build(BuildContext context) {
    if (location.isEmpty) return const Center(child: Text('No kitchen set up yet.'));
    return Loader<Map<String, dynamic>>(
      future: target,
      builder: (context, t) {
        final lines = [for (final l in t['lines'] as List) Map<String, dynamic>.from(l as Map)];
        final ingredients = [for (final i in t['ingredients'] as List) Map<String, dynamic>.from(i as Map)];
        return ListView(padding: const EdgeInsets.all(16), children: [
          LocationPicker(session: widget.session, value: location, where: (l) => l['kind'] == 'kitchen', onChanged: (v) {
            location = v;
            reload();
          }),
          const SizedBox(height: 12),
          Text('Target for the week of ${t['week']}', style: Theme.of(context).textTheme.titleLarge),
          if (t['has_history'] != true) const Text('No usage history yet - the owner sets the target by hand.'),
          for (final l in lines)
            Card(
              child: ListTile(
                title: Text(l['name'].toString()),
                subtitle: Text('On hand ${fmt(l['on_hand'])}${l['batches'] != null ? ' · ${l['batches']} batches' : ''}'),
                trailing: Text(l['target'] == null ? '–' : '${fmt(l['target'])} ${l['unit']}', style: Theme.of(context).textTheme.titleMedium),
              ),
            ),
          if (ingredients.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('Ingredients to buy', style: Theme.of(context).textTheme.titleMedium),
            for (final i in ingredients) ListTile(dense: true, title: Text(i['name'].toString()), trailing: Text('${fmt(i['to_buy'])} ${i['unit']}')),
          ],
          const Divider(height: 32),
          Text('Record production', style: Theme.of(context).textTheme.titleLarge),
          QtyList(rows: [for (final l in lines) {'item_id': l['item_id'], 'name': l['name'], 'unit': l['unit']}], controllers: made, label: 'Made'),
          FilledButton(
            onPressed: () async {
              final ls = readQty(made);
              if (ls.isEmpty) return;
              final ok = await attempt(context, () => widget.api.post('/kitchen/production', {'location_id': location, 'lines': ls}), done: 'Production saved');
              if (ok != null) reload();
            },
            child: const Text('Save production run'),
          ),
          const Divider(height: 32),
          Text('Record ingredients used', style: Theme.of(context).textTheme.titleLarge),
          QtyList(
              rows: [for (final i in ingredients) {'item_id': i['item_id'], 'name': i['name'], 'unit': i['unit'], 'hint': 'target needs ${fmt(i['needed'])}'}],
              controllers: used,
              label: 'Used'),
          FilledButton(
            onPressed: () async {
              final ls = readQty(used);
              if (ls.isEmpty) return;
              final ok = await attempt(context, () => widget.api.post('/kitchen/use', {'location_id': location, 'lines': ls}), done: 'Ingredients saved');
              if (ok != null) reload();
            },
            child: const Text('Save ingredients used'),
          ),
        ]);
      },
    );
  }
}
