import React, { Fragment } from 'react'

import type { Page } from '@/payload-types'

import { ArchiveBlock } from '@/blocks/ArchiveBlock/Component'
import { CallToActionBlock } from '@/blocks/CallToAction/Component'
import { ContentBlock } from '@/blocks/Content/Component'
import { FormBlock } from '@/blocks/Form/Component'
import { MediaBlock } from '@/blocks/MediaBlock/Component'
import {
  AreasBlock,
  FaqBlock,
  LeadFormBlock,
  MarqueeBlock,
  PackagesBlock,
  ProcessBlock,
  ServicesBlock,
  StatementBlock,
  StatsBlock,
  TestimonialsBlock,
  WorkBlock,
} from '@/blocks/studio'

const studioBlocks = {
  marquee: MarqueeBlock,
  services: ServicesBlock,
  work: WorkBlock,
  packagesBlock: PackagesBlock,
  process: ProcessBlock,
  stats: StatsBlock,
  testimonials: TestimonialsBlock,
  faq: FaqBlock,
  leadForm: LeadFormBlock,
  areas: AreasBlock,
  statement: StatementBlock,
}

const templateBlocks = {
  archive: ArchiveBlock,
  content: ContentBlock,
  cta: CallToActionBlock,
  formBlock: FormBlock,
  mediaBlock: MediaBlock,
}

export const RenderBlocks: React.FC<{ blocks: Page['layout'][0][] }> = ({ blocks }) => {
  if (!blocks || !Array.isArray(blocks) || blocks.length === 0) return null
  return (
    <Fragment>
      {blocks.map((block, index) => {
        const { blockType } = block
        if (blockType in studioBlocks) {
          const Block = studioBlocks[blockType as keyof typeof studioBlocks] as React.FC<Record<string, unknown>>
          return <Block key={block.id || index} {...(block as unknown as Record<string, unknown>)} />
        }
        if (blockType in templateBlocks) {
          const Block = templateBlocks[blockType as keyof typeof templateBlocks] as React.FC<Record<string, unknown>>
          return (
            <section className="section section--tight" key={block.id || index}>
              <div className="wrap prose-studio-wrap">
                <Block {...(block as unknown as Record<string, unknown>)} disableInnerContainer />
              </div>
            </section>
          )
        }
        return null
      })}
    </Fragment>
  )
}
