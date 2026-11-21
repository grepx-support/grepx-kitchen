// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';

import 'account.dart';

/// The kitchen: this week's target per dish as rings (made so far against the target), what to buy, and recording
/// what was made and what was used.
class KitchenScreen extends StatefulWidget {
  const KitchenScreen({super.key});

  @override
  State<KitchenScreen> createState() => _KitchenScreenState();
}

class _KitchenScreenState extends State<KitchenScreen> with LoadsData {
  String location = '';
  String mode = 'made';
  final made = <String, TextEditingController>{};
  final used = <String, TextEditingController>{};

  @override
  Future<dynamic> load(Api api) {
    if (location.isEmpty) location = pickLocation(AppScope.of(context).session, (l) => l['kind'] == 'kitchen');
    return location.isEmpty ? Future.value(null) : api.get('/kitchen/target?location_id=$location');
  }

  Future<void> _save(String path, Map<String, TextEditingController> from, String done) async {
    final lines = readQty(from);
    if (lines.isEmpty) {
      showBanner('Type a quantity first');
      return;
    }
    final api = AppScope.of(context).api;
    final ok = await attempt(context, () => api.post(path, {'location_id': location, 'lines': lines}), done: done);
    if (ok == null) return;
    from.clear();
    reload();
  }

  @override
  Widget build(BuildContext context) => AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, t) {
          if (t == null) return const LargeTitlePage(title: 'Kitchen', children: [EmptyState(icon: Icons.soup_kitchen_outlined, title: 'No kitchen set up yet', text: 'The owner adds kitchens in Setup.')]);
          final lines = ((t['lines'] ?? const []) as List).cast<Map>();
          final ingredients = ((t['ingredients'] ?? const []) as List).cast<Map>();
          return LargeTitlePage(
            title: 'Kitchen',
            subtitle: 'Week of ${Fmt.day(t['week'])}',
            onRefresh: reload,
            children: [
              LocationPicker(value: location, where: (l) => l['kind'] == 'kitchen', onChanged: (v) {
                location = v;
                made.clear();
                used.clear();
                reload();
              }),
              if (t['has_history'] != true)
                Padding(padding: const EdgeInsets.only(top: Gap.m), child: Text('No usage history yet - the owner sets the targets by hand.', style: TextStyle(color: context.secondaryText))),
              const SectionHeader('This week'),
              if (lines.isEmpty) const EmptyState(icon: Icons.restaurant_menu_rounded, title: 'No dishes yet'),
              if (lines.isNotEmpty)
                SizedBox(
                  height: 168,
                  child: ListView(scrollDirection: Axis.horizontal, clipBehavior: Clip.none, children: [
                    for (final l in lines) Padding(padding: const EdgeInsets.only(right: Gap.m), child: _TargetTile(l)),
                  ]),
                ),
              if (ingredients.isNotEmpty) ...[
                const SectionHeader('To buy'),
                GroupedList(children: [
                  for (final i in ingredients)
                    RowItem(title: '${i['name']}', icon: Icons.shopping_basket_rounded, iconColor: SystemColors.orange, value: '${qty(i['to_buy'])} ${i['unit'] ?? ''}'),
                ]),
              ],
              const SectionHeader('Record'),
              Segments<String>(value: mode, options: const {'made': 'What we made', 'used': 'What we used'}, onChanged: (v) => setState(() => mode = v)),
              const SizedBox(height: Gap.m),
              if (mode == 'made') ...[
                QtyList(rows: [for (final l in lines) {'item_id': l['item_id'], 'name': l['name'], 'unit': l['unit'], 'hint': 'on hand ${qty(l['on_hand'])}'}], controllers: made),
                const SizedBox(height: Gap.m),
                FilledButton(onPressed: () => _save('/kitchen/production', made, 'Production saved'), child: const Text('Save production')),
              ] else ...[
                QtyList(rows: [for (final i in ingredients) {'item_id': i['item_id'], 'name': i['name'], 'unit': i['unit'], 'hint': 'target needs ${qty(i['needed'])}'}], controllers: used),
                const SizedBox(height: Gap.m),
                FilledButton(onPressed: () => _save('/kitchen/use', used, 'Ingredients saved'), child: const Text('Save ingredients used')),
              ],
            ],
          );
        },
      );
}

/// A dish: a ring of on-hand against the week's target.
class _TargetTile extends StatelessWidget {
  const _TargetTile(this.l);
  final Map l;

  @override
  Widget build(BuildContext context) {
    final target = Fmt.number(l['target']);
    final onHand = Fmt.number(l['on_hand']);
    final share = target <= 0 ? 0.0 : (onHand / target).clamp(0, 1).toDouble();
    return SizedBox(
      width: 140,
      child: SoftCard(
        child: Column(children: [
          Ring(
            progress: share,
            color: share >= 1 ? SystemColors.green : (share < 0.3 ? SystemColors.orange : context.brand),
            size: 76,
            stroke: 9,
            center: Text('${(share * 100).round()}%', style: const TextStyle(fontWeight: FontWeight.w700)),
          ),
          const SizedBox(height: Gap.s),
          Text('${l['name']}', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600)),
          Text(l['target'] == null ? 'no target' : '${qty(onHand)} / ${qty(target)} ${l['unit'] ?? ''}', style: TextStyle(fontSize: 12, color: context.secondaryText)),
        ]),
      ),
    );
  }
}
