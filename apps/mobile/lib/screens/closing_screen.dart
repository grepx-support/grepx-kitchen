// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/session.dart';
import '../core/ui.dart';

/// CLS-01..09: count (expected shown), sales by type, issues, review, submit.
class ClosingScreen extends StatefulWidget {
  const ClosingScreen({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  State<ClosingScreen> createState() => _ClosingScreenState();
}

class _ClosingScreenState extends State<ClosingScreen> {
  late String location = pickLocation(widget.session, (l) => l['kind'] != 'warehouse');
  late Future<Map<String, dynamic>> form = load();
  final counts = <String, TextEditingController>{};
  final sales = <String, TextEditingController>{};
  final issues = TextEditingController();

  Future<Map<String, dynamic>> load() async => await widget.api.get('/closing/form?location_id=$location') as Map<String, dynamic>;

  void reload() => setState(() {
        counts.clear();
        sales.clear();
        issues.clear();
        form = load();
      });

  Future<void> review(Map<String, dynamic> f) async {
    final c = readQty(counts, keepZero: true);
    final s = {for (final e in sales.entries) if (double.tryParse(e.value.text.trim()) != null) e.key: double.parse(e.value.text.trim())};
    final total = s.values.fold<double>(0, (a, b) => a + b);
    final go = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Check before you submit'),
        content: Text('${c.length} items counted\nSales: ${fmt(total)}${issues.text.trim().isEmpty ? '' : '\nIssues noted'}'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Back')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Submit')),
        ],
      ),
    );
    if (go != true || !mounted) return;
    final ok = await attempt(context,
        () => widget.api.post('/closing', {'location_id': location, 'counts': c, 'sales': s, 'issues': issues.text.trim(), 'staff_name': widget.session.name}),
        done: 'Closing submitted - thank you');
    if (ok != null) reload();
  }

  @override
  Widget build(BuildContext context) {
    if (location.isEmpty) return const Center(child: Text('No location set up yet.'));
    return Loader<Map<String, dynamic>>(
      future: form,
      builder: (context, f) {
        final picker = LocationPicker(session: widget.session, value: location, where: (l) => l['kind'] != 'warehouse', onChanged: (v) {
          location = v;
          reload();
        });
        if (f['submitted_today'] == true) {
          return ListView(padding: const EdgeInsets.all(16), children: [picker, const SizedBox(height: 24), const Text('Done for today ✓')]);
        }
        final lines = [for (final l in f['lines'] as List) Map<String, dynamic>.from(l as Map)];
        return ListView(padding: const EdgeInsets.all(16), children: [
          picker,
          const SizedBox(height: 12),
          Text('1. Count', style: Theme.of(context).textTheme.titleLarge),
          const Text('Type what you count. Leave empty what you did not count.'),
          QtyList(
              rows: [for (final l in lines) {'item_id': l['item_id'], 'name': l['item_name'], 'unit': l['unit'], 'hint': 'expected ${fmt(l['expected'])}'}],
              controllers: counts,
              label: 'Counted'),
          const SizedBox(height: 12),
          Text('2. Sales', style: Theme.of(context).textTheme.titleLarge),
          for (final t in (f['sales_types'] as List))
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: TextField(
                controller: sales.putIfAbsent(t.toString(), () => TextEditingController()),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: t.toString(), border: const OutlineInputBorder()),
              ),
            ),
          const SizedBox(height: 12),
          Text('3. Issues', style: Theme.of(context).textTheme.titleLarge),
          TextField(controller: issues, maxLines: 3, decoration: const InputDecoration(hintText: 'Anything the owner should know', border: OutlineInputBorder())),
          const SizedBox(height: 16),
          FilledButton(onPressed: () => review(f), child: const Text('Check and submit')),
        ]);
      },
    );
  }
}
