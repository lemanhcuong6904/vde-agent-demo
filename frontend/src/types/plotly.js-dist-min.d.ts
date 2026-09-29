declare module "plotly.js-dist-min" {
  type PlotlyFigureData = Record<string, unknown>;
  type PlotlyLayout = Record<string, unknown>;
  type PlotlyConfig = Record<string, unknown>;

  const Plotly: {
    newPlot(
      element: HTMLElement,
      data: PlotlyFigureData[],
      layout?: PlotlyLayout,
      config?: PlotlyConfig,
    ): Promise<unknown>;
    purge(element: HTMLElement): void;
  };

  export default Plotly;
}

declare module "mathjax/es5/tex-svg.js";
