// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/ui.dart';

/// What left the warehouse, by trip - the delivery person's list (never the production plan).
class DeliveriesScreen extends StatelessWidget {
  const DeliveriesScreen({super.key, required this.api});
  final Api api;

  @override
  Widget build(BuildContext context) => Loader<dynamic>(
        future: api.get('/stock/deliveries'),
        builder: (context, data) {
          final trips = [for (final t in (data as Map)['deliveries'] as List) Map<String, dynamic>.from(t as Map)];
          if (trips.isEmpty) return const Center(child: Text('Nothing has left the warehouse yet.'));
          return ListView(padding: const EdgeInsets.all(16), children: [
            for (final t in trips)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('${t['from']} → ${t['to']}', style: Theme.of(context).textTheme.titleMedium),
                    Text('${t['date']} · sent by ${t['by']}'),
                    for (final l in t['lines'] as List) Text('${fmt((l as Map)['qty'])} ${l['unit']}  ${l['item_name']}'),
                  ]),
                ),
              ),
          ]);
        },
      );
}
