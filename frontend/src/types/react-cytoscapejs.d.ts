declare module 'react-cytoscapejs' {
  import type { ComponentType, CSSProperties } from 'react'
  import type { ElementDefinition, LayoutOptions, StylesheetStyle } from 'cytoscape'

  export interface CytoscapeComponentProps {
    elements: ElementDefinition[]
    stylesheet?: StylesheetStyle[]
    layout?: LayoutOptions
    style?: CSSProperties
    className?: string
    cy?: (cy: import('cytoscape').Core) => void
  }

  const CytoscapeComponent: ComponentType<CytoscapeComponentProps>
  export default CytoscapeComponent
}
