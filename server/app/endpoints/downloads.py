#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""ASF Infrastructure Reporting Dashboard"""

"""Handler for download stats - ported from https://github.com/apache/infrastructure-dlstats"""
import quart
from ..lib import middleware, config, asfuid
from ..plugins import downloads

@asfuid.session_required
async def process(form_data):
    project = form_data.get("project", "httpd")    # Project/podling to fetch stats for
    duration = form_data.get("duration", 7)        # Timespan to search (in whole days)
    filters = form_data.get("filters", "empty_ua,no_query") # Various search filters
    add_metadata = form_data.get("meta", "no")
    stats, params = await downloads.generate_stats(project, duration, filters)
    if add_metadata == "yes":
        return {
            "query": params,
            "files": stats,
        }
    return stats


quart.current_app.add_url_rule(
    "/api/downloads",
    methods=[
        "GET",  # Session get/delete
    ],
    view_func=middleware.glued(process),
)


