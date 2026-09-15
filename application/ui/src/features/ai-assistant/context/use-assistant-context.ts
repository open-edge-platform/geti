// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';

import { $api } from '@/api';

/**
 * Facts about the open project that are cheap enough to put in every prompt, so
 * the assistant can answer simple questions without spending a tool round-trip.
 * Anything deeper (models, architectures, jobs) stays behind a tool call.
 */
export const useAssistantContext = (projectId: string): string => {
    const { data: project } = $api.useQuery('get', '/api/projects/{project_id}', {
        params: { path: { project_id: projectId } },
    });

    const { data: statistics } = $api.useQuery('get', '/api/projects/{project_id}/dataset/statistics', {
        params: { path: { project_id: projectId } },
    });

    return useMemo(() => {
        const lines = ['The user is on the Dataset page of the Geti desktop application.'];

        if (project === undefined) {
            lines.push(`Open project id: ${projectId} (details are still loading).`);

            return lines.join('\n');
        }

        const labels = (project.task.labels ?? []).map((label) => label.name);

        lines.push(
            `Open project: "${project.name}" (id: ${project.id}), task: ${project.task.task_type}.`,
            `Labels (${labels.length}): ${labels.length === 0 ? 'none defined yet' : labels.join(', ')}.`
        );

        if (statistics !== undefined) {
            const { media_counts: media, annotations_counts: annotations } = statistics;

            lines.push(
                `Dataset: ${media.images} images, ${media.videos} videos, ${media.video_frames} video frames.`,
                `Annotated: ${annotations.annotated_images} images, ${annotations.annotated_videos} videos, ` +
                    `${annotations.instances} annotated instances in total.`
            );
        }

        return lines.join('\n');
    }, [project, statistics, projectId]);
};
