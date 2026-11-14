// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import 'session.dart';

/// Load-with-spinner, pull-to-refresh friendly.
class Loader<T> extends StatelessWidget {
  const Loader({super.key, required this.future, required this.builder});
  final Future<T> future;
  final Widget Function(BuildContext, T) builder;

  @override
  Widget build(BuildContext context) => FutureBuilder<T>(
        future: future,
        builder: (context, snap) {
          if (snap.hasError) return Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('${snap.error}')));
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          return builder(context, snap.data as T);
        },
      );
}

/// Run an action; show what happened (errors keep their trace id).
Future<T?> attempt<T>(BuildContext context, Future<T> Function() action, {String? done}) async {
  final messenger = ScaffoldMessenger.of(context);
  try {
    final result = await action();
    if (done != null) messenger.showSnackBar(SnackBar(content: Text(done)));
    return result;
  } catch (e) {
    messenger.showSnackBar(SnackBar(content: Text('$e')));
    return null;
  }
}

String fmt(dynamic n) {
  if (n == null) return '–';
  final v = (n as num).toDouble();
  return v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(2);
}

/// A location picker that remembers the last choice on this phone.
class LocationPicker extends StatelessWidget {
  const LocationPicker({super.key, required this.session, required this.value, required this.onChanged, this.where});
  final Session session;
  final String value;
  final ValueChanged<String> onChanged;
  final bool Function(Map<String, dynamic>)? where;

  @override
  Widget build(BuildContext context) {
    final list = session.locations.where(where ?? (_) => true).toList();
    return DropdownButtonFormField<String>(
      value: list.any((l) => l['id'] == value) ? value : null,
      decoration: const InputDecoration(labelText: 'Location', border: OutlineInputBorder()),
      items: [for (final l in list) DropdownMenuItem(value: l['id'] as String, child: Text('${l['name']} · ${l['kind']}'))],
      onChanged: (v) {
        if (v != null) {
          session.rememberLocation(v);
          onChanged(v);
        }
      },
    );
  }
}

String pickLocation(Session s, bool Function(Map<String, dynamic>) where) {
  final list = s.locations.where(where).toList();
  if (list.isEmpty) return '';
  return list.any((l) => l['id'] == s.lastLocation) ? s.lastLocation! : list.first['id'] as String;
}

/// One number box per item; the controllers hold what the user typed.
class QtyList extends StatelessWidget {
  const QtyList({super.key, required this.rows, required this.controllers, this.label = 'Qty'});
  final List<Map<String, dynamic>> rows;
  final Map<String, TextEditingController> controllers;
  final String label;

  @override
  Widget build(BuildContext context) => Column(children: [
        for (final r in rows)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(children: [
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(r['name']?.toString() ?? ''),
                if ((r['hint'] ?? '').toString().isNotEmpty) Text(r['hint'].toString(), style: Theme.of(context).textTheme.bodySmall),
              ])),
              SizedBox(
                width: 110,
                child: TextField(
                  controller: controllers.putIfAbsent(r['item_id'] as String, () => TextEditingController(text: r['qty'] == null ? '' : fmt(r['qty']))),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(labelText: label, suffixText: r['unit']?.toString(), border: const OutlineInputBorder(), isDense: true),
                ),
              ),
            ]),
          ),
      ]);
}

List<Map<String, dynamic>> readQty(Map<String, TextEditingController> controllers, {bool keepZero = false}) => [
      for (final e in controllers.entries)
        if (e.value.text.trim().isNotEmpty && double.tryParse(e.value.text.trim()) != null && (keepZero || double.parse(e.value.text.trim()) > 0))
          {'item_id': e.key, 'qty': double.parse(e.value.text.trim())}
    ];
