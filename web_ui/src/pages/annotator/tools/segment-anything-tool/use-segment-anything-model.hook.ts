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

import { useEffect, useMemo, useRef, useState } from 'react';

import { useQuery } from '@tanstack/react-query';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { isSegmentationDomain } from '../../../../core/projects/domains';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { useLoadAIWebworker } from '../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';
import { useNextMediaItemWithImage } from '../../hooks/use-next-media-item-with-image.hook';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { SelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item.interface';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { SegmentAnythingModel } from './model/segment-anything';
import { EncodingOutput } from './model/segment-anything-encoder';
import { InteractiveAnnotationPoint } from './segment-anything.interface';

const useDecoderOutput = () => {
    const { activeDomains } = useTask();

    return useMemo(() => {
        if (activeDomains.includes(DOMAIN.DETECTION_ROTATED_BOUNDING_BOX)) {
            return ShapeType.RotatedRect;
        }

        if (activeDomains.some(isSegmentationDomain)) {
            return ShapeType.Polygon;
        }

        return ShapeType.Rect;
    }, [activeDomains]);
};

const useDecodingFn = (model: SegmentAnythingModel | undefined, encoding: EncodingOutput | undefined) => {
    const shapeType = useDecoderOutput();

    // TODO: look into returning a new "decoder model" instance that already has the encoding data
    // stored in memory, to reduce  memory usage
    return async (points: InteractiveAnnotationPoint[]) => {
        if (points.length === 0) {
            return [];
        }

        if (model === undefined) {
            return [];
        }

        if (encoding === undefined) {
            return [];
        }

        const { shapes } = await model.processDecoder(encoding, {
            points,
            boxes: [],
            ouputConfig: {
                type: shapeType,
            },
            image: undefined,
        });

        return shapes;
    };
};

const useEncodingQuery = (
    model: SegmentAnythingModel | undefined,
    selectedMediaItem: Pick<SelectedMediaItem, 'identifier' | 'image'> | undefined
) => {
    return useQuery({
        queryKey: ['segment-anything-model', 'encoding', selectedMediaItem?.identifier],
        queryFn: async () => {
            if (model === undefined) {
                throw new Error('Model not yet initialized');
            }

            if (selectedMediaItem === undefined) {
                throw new Error('Media item not selected');
            }

            return await model.processEncoder(selectedMediaItem.image);
        },
        staleTime: Infinity,
        gcTime: 3600 * 15, // WIP
        enabled: model !== undefined && selectedMediaItem !== undefined,
    });
};

const useSegmentAnythingWorker = (
    algorithmType: AlgorithmType.SEGMENT_ANYTHING_DECODER | AlgorithmType.SEGMENT_ANYTHING_ENCODER
) => {
    const { worker } = useLoadAIWebworker(algorithmType);

    const modelRef = useRef<SegmentAnythingModel>();
    const [modelIsLoading, setModelIsLoading] = useState(false);

    useEffect(() => {
        const loadWorker = async () => {
            setModelIsLoading(true);

            if (worker) {
                // @ts-expect-error Return type of worker.model is incorrect
                const model: SegmentAnythingModel = await new worker.model();

                await model.init(algorithmType);

                modelRef.current = model;
            }

            setModelIsLoading(false);
        };

        if (worker && modelRef.current === undefined && !modelIsLoading) {
            loadWorker();
        }
    }, [worker, modelIsLoading, algorithmType]);

    return modelRef.current;
};

export const useSegmentAnythingModel = () => {
    const encoderModel = useSegmentAnythingWorker(AlgorithmType.SEGMENT_ANYTHING_ENCODER);
    const decoderModel = useSegmentAnythingWorker(AlgorithmType.SEGMENT_ANYTHING_DECODER);
    const isLoading = encoderModel === undefined || decoderModel === undefined;

    const { selectedMediaItem } = useSelectedMediaItem();
    const encodingQuery = useEncodingQuery(encoderModel, selectedMediaItem);
    const decodingQueryFn = useDecodingFn(decoderModel, encodingQuery.data);

    const nextSelectedMediaItem = useNextMediaItemWithImage();
    useEncodingQuery(encoderModel, encodingQuery.isFetching ? undefined : nextSelectedMediaItem);

    return { isLoading, encodingQuery, decodingQueryFn };
};
