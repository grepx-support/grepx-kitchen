// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:grepx_app/grepx_app.dart';

/// The signed-in person's business: its name, modules and locations (kitchens, stores, trucks, the warehouse) -
/// loaded after sign-in and again on Today, kept in the session.

Future<void> loadAccount(Api api, Session s) async {
  final me = await loadProfile(api, s);                     // name, role, permissions (shared)
  final noBusiness = me['tenant'] == null || me['tenant'] == '';
  await s.setJson('business', noBusiness ? <String, dynamic>{} : await api.get('/me/business'));
}

Map business(Session s) => (s.json('business') ?? const {}) as Map;
String businessName(Session s) => '${(business(s)['business'] as Map?)?['name'] ?? ''}';
bool moduleOn(Session s, String module) => ((business(s)['business'] as Map?)?['modules'] as Map?)?[module] != false;
List<Map> locations(Session s) => [for (final l in (business(s)['locations'] as List? ?? const [])) l as Map];

/// The location to start on: the last one picked, else the first that fits.
String pickLocation(Session s, bool Function(Map) where) {
  final list = locations(s).where(where).toList();
  if (list.isEmpty) return '';
  final last = s.prefs.getString('kitchen.location');
  return list.any((l) => l['id'] == last) ? last! : '${list.first['id']}';
}

IconData locationIcon(Object? kind) => switch ('$kind') {
      'kitchen' => Icons.soup_kitchen_rounded,
      'warehouse' => Icons.warehouse_rounded,
      'truck' => Icons.local_shipping_rounded,
      _ => Icons.storefront_rounded,
    };

/// Locations as a row of chips to swipe through; the picked one filled.
class LocationPicker extends StatelessWidget {
  const LocationPicker({super.key, required this.value, required this.onChanged, this.where});
  final String value;
  final ValueChanged<String> onChanged;
  final bool Function(Map)? where;

  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context).session;
    final list = locations(s).where(where ?? (_) => true).toList();
    if (list.length < 2) return const SizedBox.shrink();
    return SizedBox(
      height: 44,
      child: ListView(scrollDirection: Axis.horizontal, children: [
        for (final l in list)
          Padding(
            padding: const EdgeInsets.only(right: Gap.s),
            child: Pressable(
              onTap: () {
                s.prefs.setString('kitchen.location', '${l['id']}');
                onChanged('${l['id']}');
              },
              child: AnimatedContainer(
                duration: Motion.fast,
                padding: const EdgeInsets.symmetric(horizontal: 14),
                decoration: BoxDecoration(color: l['id'] == value ? context.brand : context.cardColor, borderRadius: Corner.all(22)),
                child: Row(children: [
                  Icon(locationIcon(l['kind']), size: 18, color: l['id'] == value ? Colors.white : context.brand),
                  const SizedBox(width: 6),
                  Text('${l['name']}', style: TextStyle(fontWeight: FontWeight.w600, color: l['id'] == value ? Colors.white : null)),
                ]),
              ),
            ),
          ),
      ]),
    );
  }
}

String qty(Object? n) {
  final v = Fmt.number(n).toDouble();
  return v == v.roundToDouble() ? '${v.toInt()}' : v.toStringAsFixed(2);
}

/// Items with a quantity each: the name, a hint (expected, on hand), and a number field between − and + steppers.
class QtyList extends StatelessWidget {
  const QtyList({super.key, required this.rows, required this.controllers, this.step = 1});
  final List<Map> rows;
  final Map<String, TextEditingController> controllers;
  final num step;

  @override
  Widget build(BuildContext context) => GroupedList(children: [
        for (final r in rows)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: Gap.l, vertical: Gap.s),
            child: Row(children: [
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('${r['name'] ?? ''}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
                  if ('${r['hint'] ?? ''}'.isNotEmpty) Text('${r['hint']}', style: TextStyle(fontSize: 12, color: context.secondaryText)),
                ]),
              ),
              _Stepper(
                controller: controllers.putIfAbsent('${r['item_id']}', () => TextEditingController(text: r['qty'] == null ? '' : qty(r['qty']))),
                unit: '${r['unit'] ?? ''}',
                step: step,
              ),
            ]),
          ),
      ]);
}

class _Stepper extends StatelessWidget {
  const _Stepper({required this.controller, required this.unit, required this.step});
  final TextEditingController controller;
  final String unit;
  final num step;

  void _add(num d) {
    HapticFeedback.selectionClick();
    final v = (num.tryParse(controller.text.trim()) ?? 0) + d;
    controller.text = qty(v < 0 ? 0 : v);
  }

  @override
  Widget build(BuildContext context) => Container(
        decoration: BoxDecoration(color: SystemColors.raised(Theme.of(context).brightness), borderRadius: Corner.all(12)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          IconButton(visualDensity: VisualDensity.compact, icon: const Icon(Icons.remove_rounded, size: 18), onPressed: () => _add(-step)),
          SizedBox(
            width: 64,
            child: TextField(
              controller: controller,
              textAlign: TextAlign.center,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
              decoration: InputDecoration(isDense: true, filled: false, border: InputBorder.none, hintText: '–', suffixText: unit, suffixStyle: TextStyle(fontSize: 11, color: context.secondaryText)),
            ),
          ),
          IconButton(visualDensity: VisualDensity.compact, icon: const Icon(Icons.add_rounded, size: 18), onPressed: () => _add(step)),
        ]),
      );
}

List<Map<String, dynamic>> readQty(Map<String, TextEditingController> controllers, {bool keepZero = false}) => [
      for (final e in controllers.entries)
        if (double.tryParse(e.value.text.trim()) != null && (keepZero || double.parse(e.value.text.trim()) > 0))
          {'item_id': e.key, 'qty': double.parse(e.value.text.trim())},
    ];
