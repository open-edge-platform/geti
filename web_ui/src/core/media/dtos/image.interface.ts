// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { BaseMediaDTO } from './base.interface';

export interface ImageMediaInformationDTO {
    display_url: string;
    height: number;
    width: number;
    size: number;
}

export interface ImageMediaDTO extends BaseMediaDTO {
    type: 'image';
    media_information: ImageMediaInformationDTO;
}
