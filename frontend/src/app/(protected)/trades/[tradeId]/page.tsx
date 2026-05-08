import { TradeDetailPage } from '../../../../screens/TradeDetailPage'

type Props = {
  params: Promise<{ tradeId: string }>
}

export default async function Page({ params }: Props) {
  const { tradeId } = await params
  return <TradeDetailPage tradeId={tradeId} />
}
