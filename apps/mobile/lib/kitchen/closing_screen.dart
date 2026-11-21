// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:grepx_app/grepx_app.dart';

import 'account.dart';

/// Closing, in three steps with a progress bar: count the stock, enter the day's sales, note any issues - then a
/// summary to check before it is sent. Once sent, a big tick for the day.
class ClosingScreen extends StatefulWidget {
  const ClosingScreen({super.key});

  @override
  State<ClosingScreen> createState() => _ClosingScreenState();
}

class _ClosingScreenState extends State<ClosingScreen> with LoadsData {
  String location = '';
  int step = 0;
  final counts = <String, TextEditingController>{};
  final sales = <String, TextEditingController>{};
  final issues = TextEditingController();

  @override
  Future<dynamic> load(Api api) {
    if (location.isEmpty) location = pickLocation(AppScope.of(context).session, (l) => l['kind'] != 'warehouse');
    return location.isEmpty ? Future.value(null) : api.get('/closing/form?location_id=$location');
  }

  void _restart() {
    counts.clear();
    sales.clear();
    issues.clear();
    step = 0;
    reload();
  }

  Future<void> _submit() async {
    final scope = AppScope.of(context);
    final c = readQty(counts, keepZero: true);
    final s = {for (final e in sales.entries) if (double.tryParse(e.value.text.trim()) != null) e.key: double.parse(e.value.text.trim())};
    final total = s.values.fold<double>(0, (a, b) => a + b);
    final ok = await confirmSheet(context,
        title: 'Send the closing?', text: '${c.length} items counted · sales ${qty(total)}${issues.text.trim().isEmpty ? '' : ' · issues noted'}', ok: 'Send');
    if (!ok || !mounted) return;
    final done = await attempt(context,
        () => scope.api.post('/closing', {'location_id': location, 'counts': c, 'sales': s, 'issues': issues.text.trim(), 'staff_name': scope.session.name}),
        done: 'Closing sent - thank you');
    if (done != null) _restart();
  }

  @override
  Widget build(BuildContext context) => AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, f) {
          if (f == null) return const LargeTitlePage(title: 'Closing', children: [EmptyState(icon: Icons.storefront_outlined, title: 'No location set up yet')]);
          final picker = LocationPicker(value: location, where: (l) => l['kind'] != 'warehouse', onChanged: (v) {
            location = v;
            _restart();
          });
          if (f['submitted_today'] == true) {
            return LargeTitlePage(title: 'Closing', onRefresh: reload, children: [
              picker,
              const SizedBox(height: 40),
              Center(child: Ring(progress: 1, color: SystemColors.green, size: 140, center: const Icon(Icons.check_rounded, size: 64, color: SystemColors.green))),
              const SizedBox(height: Gap.l),
              Center(child: Text('Done for today', style: context.text.headlineSmall)),
              Center(child: Text('See you tomorrow', style: TextStyle(color: context.secondaryText))),
            ]);
          }
          final lines = ((f['lines'] ?? const []) as List).cast<Map>();
          final types = ((f['sales_types'] ?? const []) as List).map((t) => '$t').toList();
          const titles = ['Count the stock', 'Enter the sales', 'Anything to note?'];
          return LargeTitlePage(
            title: 'Closing',
            onRefresh: reload,
            children: [
              picker,
              const SizedBox(height: Gap.l),
              Row(children: [
                for (var i = 0; i < 3; i++)
                  Expanded(
                    child: AnimatedContainer(
                      duration: Motion.normal,
                      height: 5,
                      margin: const EdgeInsets.only(right: 4),
                      decoration: BoxDecoration(color: i <= step ? context.brand : context.separator, borderRadius: Corner.all(3)),
                    ),
                  ),
              ]),
              const SizedBox(height: Gap.m),
              Text('Step ${step + 1} of 3', style: TextStyle(color: context.secondaryText, fontWeight: FontWeight.w600)),
              Text(titles[step], style: context.text.headlineSmall),
              const SizedBox(height: Gap.m),
              AnimatedSwitcher(
                duration: Motion.normal,
                child: KeyedSubtree(
                  key: ValueKey(step),
                  child: switch (step) {
                    0 => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                        Text('Type what you count; leave empty what you did not.', style: TextStyle(color: context.secondaryText)),
                        const SizedBox(height: Gap.s),
                        QtyList(rows: [for (final l in lines) {'item_id': l['item_id'], 'name': l['item_name'], 'unit': l['unit'], 'hint': 'expected ${qty(l['expected'])}'}], controllers: counts),
                      ]),
                    1 => GroupedList(children: [
                        for (final t in types)
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: Gap.l, vertical: Gap.s),
                            child: TextField(
                              controller: sales.putIfAbsent(t, () => TextEditingController()),
                              keyboardType: const TextInputType.numberWithOptions(decimal: true),
                              decoration: InputDecoration(labelText: t, prefixIcon: const Icon(Icons.payments_outlined)),
                            ),
                          ),
                      ]),
                    _ => TextField(controller: issues, maxLines: 5, decoration: const InputDecoration(hintText: 'Breakages, short deliveries, anything the owner should know')),
                  },
                ),
              ).animate(key: ValueKey('step$step')).fadeIn(duration: 250.ms).slideX(begin: 0.05, end: 0),
              const SizedBox(height: Gap.xl),
              Row(children: [
                if (step > 0) ...[Expanded(child: OutlinedButton(onPressed: () => setState(() => step--), child: const Text('Back'))), const SizedBox(width: Gap.m)],
                Expanded(flex: 2, child: FilledButton(onPressed: step < 2 ? () => setState(() => step++) : _submit, child: Text(step < 2 ? 'Next' : 'Check and send'))),
              ]),
            ],
          );
        },
      );
}
