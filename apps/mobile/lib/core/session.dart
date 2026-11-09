// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// The signed-in user: token, name, permissions, business (modules, locations) - kept on the device.
class Session extends ChangeNotifier {
  Session(this._prefs);
  final SharedPreferences _prefs;

  static Future<Session> load() async => Session(await SharedPreferences.getInstance());

  String? get token => _prefs.getString('token');
  bool get signedIn => token != null;
  String get name => _prefs.getString('name') ?? '';
  List<String> get perms => _prefs.getStringList('perms') ?? const [];
  Map<String, dynamic> get business => jsonDecode(_prefs.getString('business') ?? '{}') as Map<String, dynamic>;
  String get businessName => (business['business'] as Map?)?['name']?.toString() ?? '';
  List<Map<String, dynamic>> get locations =>
      [for (final l in (business['locations'] as List? ?? const [])) Map<String, dynamic>.from(l as Map)];

  bool can(String perm) => perms.contains(perm) || perms.contains('*');
  bool moduleOn(String module) => ((business['business'] as Map?)?['modules'] as Map?)?[module] != false;

  String? get lastLocation => _prefs.getString('location');
  Future<void> rememberLocation(String id) => _prefs.setString('location', id);

  /// Keep the token for the calls that load the profile (no listeners told yet).
  Future<void> useToken(String token) => _prefs.setString('token', token);

  Future<void> save(String token, Map<String, dynamic> me, Map<String, dynamic> business) async {
    await _prefs.setString('token', token);
    await _prefs.setString('name', me['name']?.toString() ?? '');
    await _prefs.setStringList('perms', [for (final p in (me['perms'] as List? ?? const [])) p.toString()]);
    await _prefs.setString('business', jsonEncode(business));
    notifyListeners();
  }

  Future<void> refresh(Map<String, dynamic> me, Map<String, dynamic> business) async {
    await _prefs.setStringList('perms', [for (final p in (me['perms'] as List? ?? const [])) p.toString()]);
    await _prefs.setString('business', jsonEncode(business));
    notifyListeners();
  }

  Future<void> clear() async {
    for (final k in ['token', 'name', 'perms', 'business']) {
      await _prefs.remove(k);
    }
    notifyListeners();
  }
}
