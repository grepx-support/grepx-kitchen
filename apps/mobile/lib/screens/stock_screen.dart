// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/ui.dart';

/// Stock at every location (INV-01).
class StockScreen extends StatelessWidget {
  const StockScreen({super.key, required this.api});
  final Api api;

  @override
  Widget build(BuildContext context) => Loader<dynamic>(
        future: api.get('/stock'),
        builder: (context, data) {
          final rows = [for (final r in (data as Map)['levels'] as List) Map<String, dynamic>.from(r as Map)];
          return ListView(children: [
            for (final r in rows)
              ListTile(dense: true, title: Text(r['item_name'].toString()), subtitle: Text(r['location_name'].toString()), trailing: Text('${fmt(r['qty'])} ${r['unit']}')),
          ]);
        },
      );
}
