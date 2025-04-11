// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { queryOptions, useMutation, useQuery } from '@tanstack/react-query';

import { Shape } from '../../../../core/annotations/shapes.interface';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { removeOffLimitPoints } from '../utils';
import { InteractiveAnnotationPoint } from './segment-anything.interface';

export const useDecodingQueryOptions = (
    points: InteractiveAnnotationPoint[],
    queryFn: (points: InteractiveAnnotationPoint[]) => Promise<Shape[]>
) => {
    const { selectedMediaItem } = useSelectedMediaItem();
    const { roi } = useROI();

    // Round points so that when the user slightly moves their mouse we do not
    // immediately recompute the decoding
    const roundedPoints = points.map((point) => ({
        x: Math.round(point.x),
        y: Math.round(point.y),
        positive: point.positive,
    }));

    return queryOptions({
        queryKey: ['segment-anything-model', 'decoding', selectedMediaItem?.identifier, roundedPoints, roi],
        queryFn: async () => {
            const shapes = await queryFn(roundedPoints);

            return shapes.map((shape) => {
                return removeOffLimitPoints(shape, roi);
            });
        },
        staleTime: Infinity,
        // TODO: Investigate why unit tests fail when keepPreviousData is used
        // One thing that I noticed is that when keepPreviousData is used, the result of the latest queryFn call
        // is not returned as `data`.
        // placeholderData: keepPreviousData,
        retry: 0,
    });
};

export const useDecodingQuery = (
    points: InteractiveAnnotationPoint[],
    queryFn: (points: InteractiveAnnotationPoint[]) => Promise<Shape[]>
) => {
    const decodingQueryOptions = useDecodingQueryOptions(points, queryFn);

    return useQuery(decodingQueryOptions);
};

export const useDecodingMutation = (queryFn: (points: InteractiveAnnotationPoint[]) => Promise<Shape[]>) => {
    const { roi } = useROI();
    const { addShapes } = useAnnotationScene();

    return useMutation({
        mutationFn: async (points: InteractiveAnnotationPoint[]) => {
            // Round points so that when the user slightly moves their mouse we do not
            // immediately recompute the decoding
            const roundedPoints = points.map((point) => ({
                x: Math.round(point.x),
                y: Math.round(point.y),
                positive: point.positive,
            }));

            const shapes = (await queryFn(roundedPoints)).map((shape) => {
                return removeOffLimitPoints(shape, roi);
            });

            addShapes(shapes);
        },
    });
};
