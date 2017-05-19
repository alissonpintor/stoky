#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import app
import os

if __name__ == '__main__':
	if os.environ.get('APP_LOCATION') == 'heroku':
		app.run(app=app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
	else:
		app.run(host='0.0.0.0', port=5000, debug=True)
