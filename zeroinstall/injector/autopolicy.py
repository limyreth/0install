"""
A simple non-interactive policy.

This module provides a simple policy that will select, download and run a suitable set of
implementations. It is not interactive. This is the policy used when you run B{0launch -c}, and
is also the policy used to run the injector's GUI.

@deprecated: The interesting functionality has moved into the L{policy.Policy} base-class.
"""

# Copyright (C) 2006, Thomas Leonard
# See the README file for details, or visit http://0install.net.

import os
from logging import debug, info, warn

from zeroinstall.support import tasks
from zeroinstall.injector import model, policy, run
from zeroinstall.injector.handler import Handler
from zeroinstall import NeedDownload

class AutoPolicy(policy.Policy):
	__slots__ = ['download_only']

	def __init__(self, interface_uri, download_only = False, dry_run = False, src = False, handler = None):
		"""@param handler: (new in 0.30) handler to use, or None to create a L{Handler}"""
		handler = handler or Handler()
		if dry_run:
			info("Note: dry_run is deprecated. Pass it to the handler instead!")
			handler.dry_run = True
		policy.Policy.__init__(self, interface_uri, handler, src = src)
		self.download_only = download_only

	def execute(self, prog_args, main = None, wrapper = None):
		downloaded = self.download_uncached_implementations()
		if downloaded:
			self.handler.wait_for_blocker(downloaded)
		if not self.download_only:
			run.execute(self, prog_args, dry_run = self.handler.dry_run, main = main, wrapper = wrapper)
		else:
			info("Downloads done (download-only mode)")
	
	def download_and_execute(self, prog_args, refresh = False, main = None):
		refreshed = self.solve_with_downloads(refresh)

		errors = self.handler.wait_for_blocker(refreshed)
		if errors:
			raise model.SafeException("Errors during download: " + '\n'.join(errors))

		if not self.solver.ready:
			raise model.SafeException("Can't find all required implementations:\n" +
				'\n'.join(["- %s -> %s" % (iface, self.solver.selections[iface])
					   for iface  in self.solver.selections]))
		self.execute(prog_args, main = main)
