// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/session.dart';
import '../core/ui.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController();
  final password = TextEditingController();
  bool busy = false;

  Future<void> login() async {
    setState(() => busy = true);
    await attempt(context, () async {
      final s = await widget.api.post('/auth/login', {'email': email.text.trim(), 'password': password.text}) as Map<String, dynamic>;
      final token = s['token'] as String;
      await widget.session.useToken(token);          // the next calls carry it; nothing is shown until save()
      try {
        final me = await widget.api.get('/me') as Map<String, dynamic>;
        final noBusiness = me['tenant'] == null || me['tenant'] == '';
        final business = noBusiness ? <String, dynamic>{} : await widget.api.get('/me/business') as Map<String, dynamic>;
        await widget.session.save(token, me, business);
      } catch (e) {
        await widget.session.clear();
        rethrow;
      }
    });
    if (mounted) setState(() => busy = false);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: ListView(padding: const EdgeInsets.all(24), shrinkWrap: true, children: [
                Text('Kitchen Stock & Costing', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 8),
                const Text('Sign in with the account your business gave you.'),
                const SizedBox(height: 24),
                TextField(controller: email, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder())),
                const SizedBox(height: 12),
                TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Password', border: OutlineInputBorder())),
                const SizedBox(height: 20),
                FilledButton(onPressed: busy ? null : login, child: Text(busy ? 'Signing in…' : 'Sign in')),
              ]),
            ),
          ),
        ),
      );
}
